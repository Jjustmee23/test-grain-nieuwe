from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from mill.models import ProductionData, Device
from django.db.models import Avg, Q
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix historical production data affected by gap handling issues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Run in dry-run mode without making changes',
        )
        parser.add_argument(
            '--threshold',
            type=float,
            default=5.0,
            help='Threshold multiplier for detecting problematic entries (default: 5.0)',
        )
        parser.add_argument(
            '--device-id',
            type=str,
            help='Fix only specific device ID',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        threshold = options['threshold']
        device_id = options.get('device_id')
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('HISTORICAL PRODUCTION DATA CORRECTION'))
        self.stdout.write(self.style.SUCCESS(f'Mode: {"DRY RUN" if dry_run else "LIVE UPDATE"}'))
        if device_id:
            self.stdout.write(self.style.SUCCESS(f'Device: {device_id}'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        corrector = HistoricalProductionDataCorrector(
            dry_run=dry_run, 
            threshold=threshold,
            device_id=device_id,
            stdout=self.stdout,
            style=self.style
        )
        
        corrector.run_correction()

class HistoricalProductionDataCorrector:
    def __init__(self, dry_run=True, threshold=5.0, device_id=None, stdout=None, style=None):
        self.dry_run = dry_run
        self.threshold = threshold
        self.device_id = device_id
        self.corrections_made = 0
        self.total_analyzed = 0
        self.stdout = stdout
        self.style = style
        
    def log(self, message, level='INFO'):
        """Log message to both stdout and logger"""
        if self.stdout:
            if level == 'ERROR':
                self.stdout.write(self.style.ERROR(message))
            elif level == 'WARNING':
                self.stdout.write(self.style.WARNING(message))
            elif level == 'SUCCESS':
                self.stdout.write(self.style.SUCCESS(message))
            else:
                self.stdout.write(message)
        
        getattr(logger, level.lower())(message)
    
    def get_device_average_production(self, device_id):
        """Get average daily production for a device, excluding outliers"""
        avg_data = ProductionData.objects.filter(
            device_id=device_id,
            daily_production__gt=0,
            daily_production__lt=2000  # Exclude obvious outliers
        ).aggregate(avg_daily=Avg('daily_production'))
        
        return avg_data['avg_daily'] if avg_data['avg_daily'] else 0
    
    def get_problematic_entries(self):
        """
        Find production entries that are likely affected by gap issues.
        """
        queryset = ProductionData.objects.select_related('device')
        
        if self.device_id:
            queryset = queryset.filter(device_id=self.device_id)
        
        problematic_entries = []
        
        # Get all devices to check
        devices_to_check = Device.objects.all()
        if self.device_id:
            devices_to_check = devices_to_check.filter(id=self.device_id)
        
        for device in devices_to_check:
            avg_daily = self.get_device_average_production(device.id)
            
            if avg_daily > 0:
                # Find entries that are much higher than average
                threshold_value = avg_daily * self.threshold
                
                entries = ProductionData.objects.filter(
                    device_id=device.id,
                    daily_production__gt=max(threshold_value, 500)  # At least 500 absolute threshold
                ).order_by('created_at')
                
                for entry in entries:
                    ratio_to_avg = entry.daily_production / avg_daily
                    problematic_entries.append({
                        'entry': entry,
                        'avg_daily': avg_daily,
                        'ratio_to_avg': ratio_to_avg
                    })
        
        return problematic_entries
    
    def analyze_gap_for_entry(self, entry_data):
        """
        Analyze a problematic entry to determine if it's likely a gap issue
        """
        entry = entry_data['entry']
        
        # Find the previous entry for this device
        prev_entry = ProductionData.objects.filter(
            device_id=entry.device_id,
            created_at__lt=entry.created_at
        ).order_by('-created_at').first()
        
        if not prev_entry:
            return None
        
        # Calculate gap in days
        entry_date = entry.created_at.date()
        prev_date = prev_entry.created_at.date()
        gap_days = (entry_date - prev_date).days
        
        # If gap is more than 1 day, this could be a gap issue
        if gap_days > 1:
            return {
                'gap_days': gap_days,
                'prev_entry': prev_entry,
                'estimated_daily': entry.daily_production / gap_days,
                'is_gap_issue': True,
                'gap_type': 'time_gap'
            }
        
        # Check if the production is way higher than normal even without a time gap
        if entry_data['ratio_to_avg'] > 10:
            # Estimate gap based on production ratio
            estimated_gap_days = min(30, max(2, int(entry_data['ratio_to_avg'] / 2)))
            return {
                'gap_days': estimated_gap_days,
                'prev_entry': prev_entry,
                'estimated_daily': entry.daily_production / estimated_gap_days,
                'is_gap_issue': True,
                'gap_type': 'value_spike'
            }
        
        return None
    
    def create_backfill_entries(self, device_id, start_date, end_date, daily_production, base_entry):
        """
        Create backfill entries for the gap period.
        """
        if self.dry_run:
            return
        
        current_date = start_date + timedelta(days=1)
        created_entries = 0
        
        while current_date < end_date:
            # Calculate cumulative values for this backfill entry
            monday_of_week = current_date - timedelta(days=current_date.weekday())
            
            weekly_production = daily_production
            monthly_production = daily_production
            yearly_production = daily_production
            
            # Add to previous values if in same period
            if base_entry.created_at.date() >= monday_of_week:
                weekly_production += base_entry.weekly_production
            if base_entry.created_at.month == current_date.month:
                monthly_production += base_entry.monthly_production
            if base_entry.created_at.year == current_date.year:
                yearly_production += base_entry.yearly_production
            
            backfill_datetime = timezone.make_aware(
                datetime.combine(current_date, datetime.min.time())
            )
            
            ProductionData.objects.create(
                device_id=device_id,
                daily_production=daily_production,
                weekly_production=weekly_production,
                monthly_production=monthly_production,
                yearly_production=yearly_production,
                created_at=backfill_datetime
            )
            
            created_entries += 1
            current_date += timedelta(days=1)
        
        if created_entries > 0:
            self.log(f"    Created {created_entries} backfill entries")
    
    def correct_entry(self, entry_data, gap_analysis):
        """
        Correct a problematic entry by redistributing the production across the gap period.
        """
        if not gap_analysis or not gap_analysis['is_gap_issue']:
            return False
        
        entry = entry_data['entry']
        gap_days = gap_analysis['gap_days']
        estimated_daily = gap_analysis['estimated_daily']
        prev_entry = gap_analysis['prev_entry']
        
        self.log(f"  Correcting entry for device {entry.device_id} on {entry.created_at.date()}")
        self.log(f"    Original daily production: {entry.daily_production}")
        self.log(f"    Gap type: {gap_analysis['gap_type']}")
        self.log(f"    Estimated gap days: {gap_days}")
        self.log(f"    New daily production: {estimated_daily:.2f}")
        
        if self.dry_run:
            self.log("    [DRY RUN] Would update production data")
            return True
        
        try:
            with transaction.atomic():
                # Calculate new cumulative values
                today = entry.created_at.date()
                monday_of_this_week = today - timedelta(days=today.weekday())
                
                # Update the entry with distributed daily production
                old_daily = entry.daily_production
                entry.daily_production = estimated_daily
                
                # Recalculate cumulative values
                if prev_entry.created_at.date() < monday_of_this_week:
                    entry.weekly_production = estimated_daily
                else:
                    entry.weekly_production = prev_entry.weekly_production + estimated_daily
                
                if prev_entry.created_at.month != today.month:
                    entry.monthly_production = estimated_daily
                else:
                    entry.monthly_production = prev_entry.monthly_production + estimated_daily
                
                if prev_entry.created_at.year != today.year:
                    entry.yearly_production = estimated_daily
                else:
                    entry.yearly_production = prev_entry.yearly_production + estimated_daily
                
                entry.save()
                
                # Create backfill entries for the gap period (if gap > 2 days)
                if gap_days > 2:
                    self.create_backfill_entries(
                        entry.device_id,
                        prev_entry.created_at.date(),
                        entry.created_at.date(),
                        estimated_daily,
                        prev_entry
                    )
                
                self.log(f"    ✓ Successfully corrected entry for device {entry.device_id}", 'SUCCESS')
                return True
                
        except Exception as e:
            self.log(f"    ✗ Error correcting entry for device {entry.device_id}: {str(e)}", 'ERROR')
            return False
    
    def run_correction(self):
        """
        Main method to run the historical data correction.
        """
        # Find problematic entries
        self.log("Step 1: Finding problematic production entries...")
        problematic_entries = self.get_problematic_entries()
        
        self.log(f"Found {len(problematic_entries)} potentially problematic entries")
        
        if not problematic_entries:
            self.log("No problematic entries found. Historical data appears correct.", 'SUCCESS')
            return
        
        # Show summary of what will be analyzed
        devices_affected = set(entry['entry'].device_id for entry in problematic_entries)
        self.log(f"Devices affected: {len(devices_affected)}")
        
        # Analyze and correct each entry
        self.log("Step 2: Analyzing and correcting entries...")
        
        for entry_data in problematic_entries:
            self.total_analyzed += 1
            entry = entry_data['entry']
            
            self.log(f"\nAnalyzing entry {self.total_analyzed}/{len(problematic_entries)}")
            self.log(f"Device: {entry.device_id}, Date: {entry.created_at.date()}")
            self.log(f"Daily Production: {entry.daily_production}, Ratio to avg: {entry_data['ratio_to_avg']:.1f}x")
            
            # Analyze the gap
            gap_analysis = self.analyze_gap_for_entry(entry_data)
            
            if gap_analysis and gap_analysis['is_gap_issue']:
                if self.correct_entry(entry_data, gap_analysis):
                    self.corrections_made += 1
            else:
                self.log("  → No gap issue detected, skipping")
        
        # Summary
        self.log("\n" + "=" * 60)
        self.log("CORRECTION SUMMARY", 'INFO')
        self.log("=" * 60)
        self.log(f"Total entries analyzed: {self.total_analyzed}")
        self.log(f"Corrections made: {self.corrections_made}")
        self.log(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE UPDATE'}")
        
        if self.dry_run:
            self.log("\n⚠️  This was a DRY RUN. No actual changes were made.", 'WARNING')
            self.log("   Run without --dry-run to apply the corrections.")
        else:
            self.log(f"\n✅ Historical data correction completed!", 'SUCCESS')
            self.log(f"   {self.corrections_made} production entries have been corrected.")
            
            if self.corrections_made > 0:
                self.log("\n📊 Next steps:")
                self.log("1. Check the corrected data in your dashboard")
                self.log("2. Verify that daily/weekly/monthly values look realistic")
                self.log("3. Monitor future data to ensure the gap handling is working") 