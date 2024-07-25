from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from django.db.models import Q
from locations.models import Location
from configuration.models import GeneralSetting


class Command(BaseCommand):
    help = 'Checks locations and updates their status to "To Check" if needed'

    def handle(self, *args, **options):
        settings = GeneralSetting.load()
        checking_period = settings.checking_period
        now = make_aware(datetime.now())

        locations_to_check = Location.objects.filter(
            Q(last_checked__lt=now - timedelta(days=checking_period)) |
            Q(last_checked__isnull=True, updated__lt=now - timedelta(days=checking_period)),
            status__in=['visible', 'hidden']
        )

        count = locations_to_check.update(status='to_check')
        self.stdout.write(self.style.SUCCESS(f'Updated {count} locations to "To Check" status.'))
