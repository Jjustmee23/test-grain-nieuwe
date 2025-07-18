from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from mill.models import Batch, RawData
import random
from django.db.models.signals import post_save
from mill import signals
from mill.models import Batch
from contextlib import contextmanager

@contextmanager
def disconnect_batch_signals():
    from django.db.models.signals import post_save
    from mill import signals
    from mill.models import Batch
    post_save.disconnect(signals.notify_on_batch_completion, sender=Batch)
    post_save.disconnect(signals.notify_on_batch_status_change, sender=Batch)
    post_save.disconnect(signals.notify_admins_on_batch_acceptance, sender=Batch)
    try:
        yield
    finally:
        post_save.connect(signals.notify_on_batch_completion, sender=Batch)
        post_save.connect(signals.notify_on_batch_status_change, sender=Batch)
        post_save.connect(signals.notify_admins_on_batch_acceptance, sender=Batch)

class Command(BaseCommand):
    help = 'Update all batches: set start_date to a random day in the past month, set start_value to the device counter on that day, set current_value to the difference with the current device counter, en set status to approved.'

    def handle(self, *args, **options):
        with disconnect_batch_signals():
            batches = Batch.objects.all()
            if not batches.exists():
                self.stdout.write(self.style.WARNING('No batches found to update.'))
                return
            self.stdout.write(self.style.SUCCESS(f'Updating {batches.count()} batches...'))
            now = timezone.now()
            updated_count = 0
            for batch in batches:
                if not batch.factory:
                    self.stdout.write(f'Skipping batch {batch.batch_number}: no factory assigned')
                    continue
                # Kies een random dag in de afgelopen maand
                days_back = random.randint(1, 30)
                start_date = now - timedelta(days=days_back)
                # Zoek het device (eerste device van de factory)
                device = batch.factory.devices.first()
                if not device:
                    self.stdout.write(f'Skipping batch {batch.batch_number}: no device for factory')
                    continue
                counter_field = device.selected_counter or 'counter_1'
                # Zoek de counter waarde op de startdatum
                start_raw = RawData.objects.filter(device=device, timestamp__lte=start_date).order_by('-timestamp').first()
                start_value = getattr(start_raw, counter_field, 0) if start_raw else 0
                # Zoek de huidige counter waarde
                now_raw = RawData.objects.filter(device=device).order_by('-timestamp').first()
                now_value = getattr(now_raw, counter_field, 0) if now_raw else start_value
                # Zet batch waarden
                batch.start_date = start_date
                batch.start_value = start_value
                batch.current_value = now_value - start_value
                batch.status = 'approved'
                # Set approved_by/approved_at
                from django.contrib.auth.models import User
                superuser = User.objects.filter(is_superuser=True).first()
                if superuser:
                    batch.approved_by = superuser
                    batch.approved_at = start_date
                batch.save()
                updated_count += 1
                self.stdout.write(f'Batch {batch.batch_number}: start_date={start_date.strftime("%Y-%m-%d")}, start_value={start_value}, now_value={now_value}, current_value={batch.current_value}')
            self.stdout.write(self.style.SUCCESS(f'Successfully updated {updated_count} batches!')) 