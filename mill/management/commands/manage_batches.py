#!/usr/bin/env python3
"""
🏭 Django Management Command - UC300 Batch Management
Complete command-line interface voor batch management

Commands:
- Start nieuwe batch
- Stop actieve batch  
- Show batch dashboard
- List batch-enabled devices
"""

from django.core.management.base import BaseCommand
from mill.services.batch_management_service import BatchManagementService
from mill.models import Device, UC300BatchStatus
from django.utils import timezone

class Command(BaseCommand):
    help = 'UC300 Batch Management System'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['start', 'stop', 'dashboard', 'list', 'status'],
            help='Action to perform'
        )
        
        parser.add_argument(
            '--device-id',
            type=str,
            help='Device ID voor batch operations'
        )
        
        parser.add_argument(
            '--batch-name',
            type=str,
            help='Batch name voor nieuwe batch'
        )
        
        parser.add_argument(
            '--no-reset',
            action='store_true',
            help='Don\'t reset counter when starting batch'
        )

    def handle(self, *args, **options):
        action = options['action']
        device_id = options.get('device_id')
        batch_name = options.get('batch_name')
        reset_counter = not options.get('no_reset', False)
        
        service = BatchManagementService()
        
        try:
            if action == 'start':
                self.handle_start_batch(service, device_id, batch_name, reset_counter)
                
            elif action == 'stop':
                self.handle_stop_batch(service, device_id)
                
            elif action == 'dashboard':
                self.handle_dashboard(service, device_id)
                
            elif action == 'list':
                self.handle_list_devices(service)
                
            elif action == 'status':
                self.handle_device_status(service, device_id)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )

    def handle_start_batch(self, service, device_id, batch_name, reset_counter):
        """Handle start batch command"""
        if not device_id:
            self.stdout.write(
                self.style.ERROR('--device-id is required for start action')
            )
            return
            
        if not batch_name:
            self.stdout.write(
                self.style.ERROR('--batch-name is required for start action')
            )
            return
        
        self.stdout.write(f'🏭 Starting batch "{batch_name}" for device {device_id}')
        self.stdout.write(f'Counter reset: {"YES" if reset_counter else "NO"}')
        
        new_batch = service.start_new_batch(device_id, batch_name, reset_counter)
        
        if new_batch:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Batch started successfully: ID {new_batch.id}')
            )
            
            # Show batch info
            self.stdout.write(f'Batch Name: {new_batch.batch_name}')
            self.stdout.write(f'Start Time: {new_batch.batch_start_time}')
            self.stdout.write(f'Start Counter: {new_batch.start_counter_value}')
        else:
            self.stdout.write(
                self.style.ERROR('❌ Failed to start batch')
            )

    def handle_stop_batch(self, service, device_id):
        """Handle stop batch command"""
        if not device_id:
            self.stdout.write(
                self.style.ERROR('--device-id is required for stop action')
            )
            return
        
        self.stdout.write(f'🛑 Stopping active batch for device {device_id}')
        
        stopped_batch = service.stop_active_batch(device_id, "manual_stop")
        
        if stopped_batch:
            production = service.calculate_batch_production(stopped_batch.id)
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Batch stopped successfully')
            )
            
            self.stdout.write(f'Batch Name: {stopped_batch.batch_name}')
            self.stdout.write(f'Total Production: {production} units')
            self.stdout.write(f'Duration: {stopped_batch.get_batch_duration()}')
        else:
            self.stdout.write(
                self.style.WARNING('⚠️ No active batch found to stop')
            )

    def handle_dashboard(self, service, device_id):
        """Handle dashboard command"""
        self.stdout.write('🏭 BATCH MANAGEMENT DASHBOARD')
        self.stdout.write('=' * 60)
        
        service.show_batch_dashboard(device_id)

    def handle_list_devices(self, service):
        """Handle list devices command"""
        devices = service.list_available_devices_for_batch()
        
        self.stdout.write(f'📋 BATCH-ENABLED DEVICES ({len(devices)})')
        self.stdout.write('=' * 50)
        
        if devices:
            for device in devices:
                pilot_status = device.pilot_status
                self.stdout.write(
                    f'• {device.name} ({device.id})'
                )
                self.stdout.write(
                    f'  Pilot: {"🟢 ACTIVE" if pilot_status.is_pilot_enabled else "⚪ INACTIVE"}'
                )
                self.stdout.write(
                    f'  Batch Reset: {"🟢 ENABLED" if pilot_status.batch_reset_enabled else "⚪ DISABLED"}'
                )
                self.stdout.write('')
        else:
            self.stdout.write('No batch-enabled devices found')

    def handle_device_status(self, service, device_id):
        """Handle device status command"""
        if not device_id:
            self.stdout.write(
                self.style.ERROR('--device-id is required for status action')
            )
            return
        
        status = service.get_batch_status_overview(device_id)
        
        if status:
            device = status['device']
            active_batch = status['active_batch']
            
            self.stdout.write(f'📊 DEVICE STATUS: {device.name}')
            self.stdout.write('=' * 50)
            
            self.stdout.write(f'Device ID: {device.id}')
            self.stdout.write(f'Current Counter: {status["current_counter"]}')
            self.stdout.write(f'Counter Timestamp: {status["counter_timestamp"]}')
            
            if active_batch:
                current_production = service.calculate_batch_production(active_batch.id)
                
                self.stdout.write(f'\n🟢 ACTIVE BATCH:')
                self.stdout.write(f'  Name: {active_batch.batch_name}')
                self.stdout.write(f'  Started: {active_batch.batch_start_time}')
                self.stdout.write(f'  Start Counter: {active_batch.start_counter_value}')
                self.stdout.write(f'  Current Production: {current_production} units')
                self.stdout.write(f'  Duration: {active_batch.get_batch_duration()}')
            else:
                self.stdout.write(f'\n⚪ No active batch')
            
            # Recent batches
            recent_batches = status['recent_batches']
            if recent_batches:
                self.stdout.write(f'\n📋 RECENT BATCHES:')
                for batch in recent_batches[:5]:
                    production = service.calculate_batch_production(batch.id)
                    status_icon = "🟢" if batch.is_active else "⚪"
                    self.stdout.write(
                        f'  {status_icon} {batch.batch_name}: {production} units'
                    )
        else:
            self.stdout.write(
                self.style.ERROR(f'Device {device_id} not found or not accessible')
            ) 