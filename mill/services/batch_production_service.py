from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Max, Min, Q
from datetime import datetime, timedelta
from decimal import Decimal
from mill.models import Batch, Device, RawData, ProductionData, TransactionData
import logging

logger = logging.getLogger(__name__)

class BatchProductionService:
    """
    Centrale service voor alle batch productie berekeningen en updates
    Consolideert alle data bronnen naar één consistente methode
    """
    
    # Conversion factor: 1 counter unit = 50 kg flour (based on template usage)
    CONVERSION_FACTOR = 50.0  # kg per counter unit
    TONS_PER_KG = 1000.0    # 1000 kg = 1 ton
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_batch_progress(self, batch):
        """
        Bereken batch progress op basis van device counter data
        Gebruikt RawData als primaire data bron
        """
        if not batch.factory:
            return {
                'current_value': 0,
                'actual_flour_output': 0.0,
                'progress_percentage': 0.0,
                'data_source': 'no_factory'
            }
        
        # Get devices for this factory
        devices = Device.objects.filter(factory=batch.factory)
        if not devices.exists():
            return {
                'current_value': 0,
                'actual_flour_output': 0.0,
                'progress_percentage': 0.0,
                'data_source': 'no_devices'
            }
        
        total_current_value = 0
        total_start_value = 0
        data_sources = []
        
        for device in devices:
            device_data = self._get_device_production_data(device, batch)
            total_current_value += device_data['current_value']
            total_start_value += device_data['start_value']
            data_sources.append(device_data['data_source'])
        
        # Calculate actual production
        production_difference = total_current_value - total_start_value
        actual_flour_output = (Decimal(str(production_difference)) * 
                              Decimal(str(self.CONVERSION_FACTOR)) / 
                              Decimal(str(self.TONS_PER_KG)))
        
        # Calculate progress percentage
        progress_percentage = 0.0
        if batch.expected_flour_output and batch.expected_flour_output > 0:
            try:
                progress_percentage = float((actual_flour_output / batch.expected_flour_output) * 100)
                progress_percentage = min(progress_percentage, 100.0)
            except Exception as e:
                self.logger.error(f"Error calculating progress for batch {batch.batch_number}: {e}")
        
        return {
            'current_value': total_current_value,
            'actual_flour_output': float(actual_flour_output),
            'progress_percentage': progress_percentage,
            'data_source': 'raw_data' if 'raw_data' in data_sources else 'production_data',
            'device_count': devices.count(),
            'last_update': timezone.now()
        }
    
    def _get_device_production_data(self, device, batch):
        """
        Haal productie data op voor een specifiek device
        Probeert RawData eerst, dan ProductionData als fallback
        """
        counter_field = device.selected_counter or 'counter_1'
        
        # Try RawData first (most accurate)
        raw_data = self._get_raw_data_for_device(device, counter_field, batch)
        if raw_data:
            return {
                'current_value': raw_data['current_value'],
                'start_value': raw_data['start_value'],
                'data_source': 'raw_data'
            }
        
        # Fallback to ProductionData
        prod_data = self._get_production_data_for_device(device, batch)
        if prod_data:
            return {
                'current_value': prod_data['current_value'],
                'start_value': prod_data['start_value'],
                'data_source': 'production_data'
            }
        
        # No data available
        return {
            'current_value': 0,
            'start_value': 0,
            'data_source': 'no_data'
        }
    
    def _get_raw_data_for_device(self, device, counter_field, batch):
        """
        Haal RawData op voor device counter berekeningen
        """
        try:
            # Validate inputs
            if not device or not counter_field or not batch:
                self.logger.warning(f"Invalid parameters for _get_raw_data_for_device: device={device}, counter_field={counter_field}, batch={batch}")
                return None
            
            # Get current counter value
            current_raw = RawData.objects.filter(
                device=device
            ).order_by('-timestamp').first()
            
            if not current_raw:
                self.logger.info(f"No RawData found for device {device.id}")
                return None
            
            # Validate counter field exists
            if not hasattr(current_raw, counter_field):
                self.logger.error(f"Counter field '{counter_field}' not found on RawData for device {device.id}")
                return None
            
            current_value = getattr(current_raw, counter_field, 0) or 0
            
            # Validate counter value is reasonable
            if current_value < 0:
                self.logger.warning(f"Negative counter value {current_value} for device {device.id}, field {counter_field}")
                current_value = 0
            
            # Get counter value at batch start
            start_raw = RawData.objects.filter(
                device=device,
                timestamp__gte=batch.start_date
            ).order_by('timestamp').first()
            
            if start_raw:
                start_value = getattr(start_raw, counter_field, 0) or 0
                if start_value < 0:
                    self.logger.warning(f"Negative start value {start_value} for device {device.id}, using 0")
                    start_value = 0
            else:
                # If no data at start, use batch start_value
                start_value = batch.start_value
                self.logger.info(f"No RawData at batch start for device {device.id}, using batch start_value: {start_value}")
            
            # Ensure current_value >= start_value (counters should only increase)
            if current_value < start_value:
                self.logger.warning(f"Current value {current_value} < start value {start_value} for device {device.id}, counter may have been reset")
                # In this case, assume counter was reset and current_value is the total production
                start_value = 0
            
            return {
                'current_value': current_value,
                'start_value': start_value,
                'timestamp': current_raw.timestamp
            }
            
        except AttributeError as e:
            self.logger.error(f"Attribute error getting RawData for device {device.id}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error getting RawData for device {device.id}: {e}")
            return None
    
    def _get_production_data_for_device(self, device, batch):
        """
        Fallback naar ProductionData als RawData niet beschikbaar is
        """
        try:
            # Get latest production data
            latest_prod = ProductionData.objects.filter(
                device=device
            ).order_by('-updated_at').first()
            
            if not latest_prod:
                return None
            
            # Use daily_production as current value
            current_value = latest_prod.daily_production or 0
            
            # For ProductionData, we need to estimate start value
            # This is less accurate than RawData
            start_value = batch.start_value
            
            return {
                'current_value': current_value,
                'start_value': start_value,
                'timestamp': latest_prod.updated_at
            }
            
        except Exception as e:
            self.logger.error(f"Error getting ProductionData for device {device.id}: {e}")
            return None
    
    def update_batch_progress(self, batch, dry_run=False):
        """
        Update batch progress met nieuwe berekeningen
        """
        try:
            progress_data = self.calculate_batch_progress(batch)
            
            if dry_run:
                return {
                    'success': True,
                    'dry_run': True,
                    'data': progress_data
                }
            
            with transaction.atomic():
                # Update batch values
                batch.current_value = progress_data['current_value']
                batch.actual_flour_output = Decimal(str(progress_data['actual_flour_output']))
                
                # Check if batch should be completed
                if (progress_data['progress_percentage'] >= 100 and 
                    batch.status not in ['completed', 'stopped']):
                    batch.status = 'completed'
                    batch.is_completed = True
                    batch.end_date = timezone.now()
                    self.logger.info(f"Batch {batch.batch_number} auto-completed")
                
                batch.save()
                
                self.logger.info(
                    f"Updated batch {batch.batch_number}: "
                    f"Progress {progress_data['progress_percentage']:.1f}%, "
                    f"Output {progress_data['actual_flour_output']:.2f} tons"
                )
                
                return {
                    'success': True,
                    'data': progress_data,
                    'batch_updated': True
                }
                
        except Exception as e:
            self.logger.error(f"Error updating batch {batch.batch_number}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_all_batches(self, dry_run=False):
        """
        Update alle actieve batches
        """
        active_batches = Batch.objects.filter(
            status__in=['approved', 'in_process', 'paused']
        )
        
        results = {
            'total': active_batches.count(),
            'updated': 0,
            'errors': 0,
            'details': []
        }
        
        for batch in active_batches:
            result = self.update_batch_progress(batch, dry_run)
            if result['success']:
                results['updated'] += 1
            else:
                results['errors'] += 1
            
            results['details'].append({
                'batch_number': batch.batch_number,
                'result': result
            })
        
        return results
    
    def get_batch_analytics(self, batch):
        """
        Haal uitgebreide analytics op voor een batch
        """
        if not batch.factory:
            return None
        
        devices = Device.objects.filter(factory=batch.factory)
        
        analytics = {
            'batch_info': {
                'batch_number': batch.batch_number,
                'factory': batch.factory.name,
                'status': batch.get_status_display(),
                'start_date': batch.start_date,
                'expected_output': float(batch.expected_flour_output),
                'waste_factor': float(batch.waste_factor)
            },
            'production_summary': self.calculate_batch_progress(batch),
            'device_summary': {
                'total_devices': devices.count(),
                'active_devices': devices.filter(status=True).count(),
                'device_details': []
            },
            'timeline': self._get_batch_timeline(batch),
            'efficiency_metrics': self._calculate_efficiency_metrics(batch)
        }
        
        # Add device details
        for device in devices:
            device_data = self._get_device_production_data(device, batch)
            analytics['device_summary']['device_details'].append({
                'device_id': device.id,
                'device_name': device.name,
                'status': device.status,
                'current_value': device_data['current_value'],
                'data_source': device_data['data_source']
            })
        
        return analytics
    
    def _get_batch_timeline(self, batch):
        """
        Haal timeline data op voor batch
        """
        timeline = []
        
        # Add key events
        if batch.created_at:
            timeline.append({
                'date': batch.created_at,
                'event': 'Batch Created',
                'description': f'Batch {batch.batch_number} created'
            })
        
        if batch.approved_at:
            timeline.append({
                'date': batch.approved_at,
                'event': 'Batch Approved',
                'description': f'Approved by {batch.approved_by.username if batch.approved_by else "Unknown"}'
            })
        
        if batch.end_date:
            timeline.append({
                'date': batch.end_date,
                'event': 'Batch Completed',
                'description': f'Batch completed with {batch.progress_percentage:.1f}% progress'
            })
        
        return sorted(timeline, key=lambda x: x['date'])
    
    def _calculate_efficiency_metrics(self, batch):
        """
        Bereken efficiency metrics voor batch
        """
        if not batch.start_date:
            return {}
        
        duration = timezone.now() - batch.start_date
        expected_duration = timedelta(days=30)  # Assume 30 days expected
        
        efficiency = {
            'duration_days': duration.days,
            'expected_duration_days': expected_duration.days,
            'time_efficiency': min(100, (expected_duration.days / max(1, duration.days)) * 100),
            'production_efficiency': batch.progress_percentage,
            'overall_efficiency': (batch.progress_percentage + 
                                 min(100, (expected_duration.days / max(1, duration.days)) * 100)) / 2
        }
        
        return efficiency 