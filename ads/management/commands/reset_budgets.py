from django.core.management.base import BaseCommand
from ads.tasks import reset_daily_monthly_spends

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        reset_daily_monthly_spends.delay()
