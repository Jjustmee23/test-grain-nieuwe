from django.core.management.base import BaseCommand
from django.db import transaction, connections
from django.utils import timezone
from datetime import datetime, timedelta
from mill.models import ProductionData, Device
from django.db.models import Avg, Q
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix historical production data using actual counter values from mqtt_data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Run in dry-run mode without making changes',
        )
        parser.add_argument(
            '--device-id',
            type=str,
            help='Fix only specific device ID',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        device_id = options.get('device_id')
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('CORRECT HISTORICAL PRODUCTION DATA CORRECTION'))
        self.stdout.write(self.style.SUCCESS('Using actual counter values from mqtt_data'))
        self.stdout.write(self.style.SUCCESS(f'Mode: {"DRY RUN" if dry_run else "LIVE UPDATE"}'))
        if device_id:
            self.stdout.write(self.style.SUCCESS(f'Device: {device_id}'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        corrector = CorrectHistoricalProductionDataCorrector(
            dry_run=dry_run, 
            device_id=device_id,
            stdout=self.stdout,
            style=self.style
        )
        
        corrector.run_correction()

class CorrectHistoricalProductionDataCorrector:
    def __init__(self, dry_run=True, device_id=None, stdout=None, style=None):
        self.dry_run = dry_run
        self.device_id = device_id
        self.corrections_made = 0
        self.total_analyzed = 0
        self.stdout = stdout
        self.style = style
        
    def log(self, message, level='INFO'):
        """Log message to stdout"""
        if self.stdout:
            if level == 'ERROR':
                self.stdout.write(self.style.ERROR(message))
            elif level == 'WARNING':
                self.stdout.write(self.style.WARNING(message))
            else:
                self.stdout.write(message)
    
    def get_counter_value_at_date(self, device_id, selected_counter, target_date):
        """Get the counter value from mqtt_data at or before a specific date"""
        try:
            with connections['counter'].cursor() as cursor:
                query = f"""
                    SELECT {selected_counter}, timestamp
                    FROM mqtt_data 
                    WHERE counter_id = %s AND DATE(timestamp) <= %s
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """
                cursor.execute(query, (device_id, target_date))
                result = cursor.fetchone()
                return result[0] if result and result[0] is not None else None
        except Exception as e:
            self.log(f"Error getting counter value for device {device_id} at {target_date}: {str(e)}", 'ERROR')
            return None
    
    def get_last_counter_value_before_date(self, device_id, selected_counter, before_date):
        """Get the last known counter value before a specific date"""
        try:
            with connections['counter'].cursor() as cursor:
                query = f"""
                    SELECT {selected_counter}, timestamp
                    FROM mqtt_data 
                    WHERE counter_id = %s AND DATE(timestamp) < %s
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """
                cursor.execute(query, (device_id, before_date))
                result = cursor.fetchone()
                if result and result[0] is not None:
                    return result[0], result[1].date()
                return None, None
        except Exception as e:
            self.log(f"Error getting last counter value for device {device_id} before {before_date}: {str(e)}", 'ERROR')
            return None, None
    
    def get_problematic_entries(self):
        """Find production entries that need to be recalculated using counter values"""
        queryset = ProductionData.objects.select_related('device')
        
        if self.device_id:
            queryset = queryset.filter(device_id=self.device_id)
        
        # Get all entries for analysis (lowered threshold to catch more cases)
        entries = queryset.filter(
            daily_production__gt=50  # Any daily production > 50 to analyze
        ).order_by('device_id', 'created_at')
        
        return list(entries)
    
    def calculate_correct_daily_production(self, entry):
        """Calculate the correct daily production using actual counter values"""
        try:
            device = entry.device
            selected_counter = device.selected_counter
            entry_date = entry.created_at.date()
            
            # Get counter value on the entry date
            current_counter = self.get_counter_value_at_date(
                device.id, selected_counter, entry_date
            )
            
            if current_counter is None:
                self.log(f"No counter data found for device {device.id} on {entry_date}", 'WARNING')
                return None
            
            # Get last known counter value before this entry
            last_counter, last_date = self.get_last_counter_value_before_date(
                device.id, selected_counter, entry_date
            )
            
            if last_counter is None:
                self.log(f"No previous counter data found for device {device.id} before {entry_date}", 'WARNING')
                return None
            
            # Calculate actual daily production
            actual_daily_production = max(0, current_counter - last_counter)
            
            return {
                'actual_daily_production': actual_daily_production,
                'current_counter': current_counter,
                'last_counter': last_counter,
                'last_date': last_date,
                'days_gap': (entry_date - last_date).days if last_date else 0
            }
            
        except Exception as e:
            self.log(f"Error calculating production for device {entry.device_id} on {entry.created_at.date()}: {str(e)}", 'ERROR')
            return None
    
    def correct_entry(self, entry, calculation_data):
        """Correct a production entry with the actual daily production"""
        if not calculation_data:
            return False
        
        actual_daily = calculation_data['actual_daily_production']
        current_counter = calculation_data['current_counter']
        last_counter = calculation_data['last_counter']
        last_date = calculation_data['last_date']
        days_gap = calculation_data['days_gap']
        
        self.log(f"Correcting entry for device {entry.device_id} on {entry.created_at.date()}")
        self.log(f"  Original daily production: {entry.daily_production}")
        self.log(f"  Counter: {last_counter} ({last_date}) → {current_counter} ({entry.created_at.date()})")
        self.log(f"  Days gap: {days_gap}")
        self.log(f"  Actual daily production: {actual_daily}")
        
        if self.dry_run:
            self.log("  [DRY RUN] Would update production data")
            return True
        
        try:
            with transaction.atomic():
                # Get previous entry for cumulative calculations
                prev_entry = ProductionData.objects.filter(
                    device_id=entry.device_id,
                    created_at__lt=entry.created_at
                ).order_by('-created_at').first()
                
                today = entry.created_at.date()
                monday_of_this_week = today - timedelta(days=today.weekday())
                
                # Update with actual daily production
                entry.daily_production = actual_daily
                
                # Recalculate cumulative values
                if prev_entry:
                    if prev_entry.created_at.date() < monday_of_this_week:
                        entry.weekly_production = actual_daily
                    else:
                        entry.weekly_production = prev_entry.weekly_production + actual_daily
                    
                    if prev_entry.created_at.month != today.month:
                        entry.monthly_production = actual_daily
                    else:
                        entry.monthly_production = prev_entry.monthly_production + actual_daily
                    
                    if prev_entry.created_at.year != today.year:
                        entry.yearly_production = actual_daily
                    else:
                        entry.yearly_production = prev_entry.yearly_production + actual_daily
                else:
                    # First entry
                    entry.weekly_production = actual_daily
                    entry.monthly_production = actual_daily
                    entry.yearly_production = actual_daily
                
                entry.save()
                
                self.log(f"  ✓ Successfully corrected entry for device {entry.device_id}")
                return True
                
        except Exception as e:
            self.log(f"  ✗ Error correcting entry for device {entry.device_id}: {str(e)}", 'ERROR')
            return False
    
    def run_correction(self):
        """Main method to run the historical data correction"""
        
        # Find problematic entries
        self.log("Step 1: Finding entries that need counter-based correction...")
        problematic_entries = self.get_problematic_entries()
        
        self.log(f"Found {len(problematic_entries)} entries to analyze")
        
        if not problematic_entries:
            self.log("No entries found that need correction.")
            return
        
        # Analyze and correct each entry
        self.log("Step 2: Analyzing entries using actual counter values...")
        
        for entry in problematic_entries:
            self.total_analyzed += 1
            
            self.log(f"\nAnalyzing entry {self.total_analyzed}/{len(problematic_entries)}")
            self.log(f"Device: {entry.device_id}, Date: {entry.created_at.date()}")
            self.log(f"Current daily production: {entry.daily_production}")
            
            # Calculate correct production using counter values
            calculation_data = self.calculate_correct_daily_production(entry)
            
            if calculation_data:
                actual_daily = calculation_data['actual_daily_production']
                
                # Only correct if there's a significant difference
                if abs(entry.daily_production - actual_daily) > 10:
                    if self.correct_entry(entry, calculation_data):
                        self.corrections_made += 1
                else:
                    self.log("  → Daily production is already correct, skipping")
            else:
                self.log("  → Could not calculate correct production, skipping")
        
        # Summary
        self.log("\n" + "=" * 60)
        self.log("CORRECTION SUMMARY")
        self.log("=" * 60)
        self.log(f"Total entries analyzed: {self.total_analyzed}")
        self.log(f"Corrections made: {self.corrections_made}")
        self.log(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE UPDATE'}")
        
        if self.dry_run:
            self.log("\n⚠️  This was a DRY RUN. No actual changes were made.", 'WARNING')
            self.log("   Run without --dry-run to apply the corrections.")
        else:
            self.log(f"\n✅ Historical data correction completed!")
            self.log(f"   {self.corrections_made} production entries have been corrected.")
            
            if self.corrections_made > 0:
                self.log("\n📊 Next steps:")
                self.log("1. Check the corrected data in your dashboard")
                self.log("2. Verify that daily values reflect actual counter differences")
                self.log("3. Monitor future data to ensure gap handling works correctly") 