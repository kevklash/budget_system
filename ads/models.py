from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import time
from typing import Final
from decimal import Decimal


class Brand(models.Model):
    name: models.CharField = models.CharField(max_length=255, unique=True)
    daily_budget: models.DecimalField = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_budget: models.DecimalField = models.DecimalField(max_digits=10, decimal_places=2)
    current_daily_spend: models.DecimalField = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    current_monthly_spend: models.DecimalField = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Brand"
        verbose_name_plural = "Brands"
        ordering = ['name']

    def __str__(self) -> str:
        return self.name

    @property
    def daily_budget_remaining(self) -> Decimal:
        """Calculate remaining daily budget."""
        return self.daily_budget - self.current_daily_spend

    @property
    def monthly_budget_remaining(self) -> Decimal:
        """Calculate remaining monthly budget."""
        return self.monthly_budget - self.current_monthly_spend

    @property
    def is_daily_budget_exceeded(self) -> bool:
        """Check if daily budget is exceeded."""
        return self.current_daily_spend >= self.daily_budget

    @property
    def is_monthly_budget_exceeded(self) -> bool:
        """Check if monthly budget is exceeded."""
        return self.current_monthly_spend >= self.monthly_budget


class Campaign(models.Model):
    name: models.CharField = models.CharField(max_length=255)
    brand: models.ForeignKey = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='campaigns')
    is_active: models.BooleanField = models.BooleanField(default=True)
    created_at: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Campaign"
        verbose_name_plural = "Campaigns"
        ordering = ['name']
        unique_together = [['name', 'brand']]

    def __str__(self) -> str:
        return f"{self.name} ({self.brand.name})"

    @property
    def total_spend_today(self) -> Decimal:
        """Calculate total spend for today."""
        today = timezone.now().date()
        return sum(
            log.amount for log in self.spend_logs.filter(
                timestamp__date=today
            )
        ) or Decimal('0.00')


class SpendLog(models.Model):
    campaign: models.ForeignKey = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='spend_logs')
    amount: models.DecimalField = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp: models.DateTimeField = models.DateTimeField(auto_now_add=True)
    description: models.TextField = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Spend Log"
        verbose_name_plural = "Spend Logs"
        ordering = ['-timestamp']

    def __str__(self) -> str:
        return f"{self.campaign.name}: ${float(self.amount):.2f} at {self.timestamp}"


class DaypartingSchedule(models.Model):
    campaign: models.OneToOneField = models.OneToOneField(Campaign, on_delete=models.CASCADE, related_name='dayparting_schedule')
    start_time: models.TimeField = models.TimeField()
    end_time: models.TimeField = models.TimeField()
    timezone: models.CharField = models.CharField(max_length=50, default='UTC')

    class Meta:
        verbose_name = "Dayparting Schedule"
        verbose_name_plural = "Dayparting Schedules"

    def __str__(self) -> str:
        return f"{self.campaign.name}: {self.start_time} - {self.end_time}"

    def is_active_now(self) -> bool:
        """Check if campaign should be active based on current time."""
        now = timezone.now().time()
        if self.start_time <= self.end_time:
            # Normal case: start_time < end_time (e.g., 09:00 - 17:00)
            return self.start_time <= now <= self.end_time
        else:
            # Overnight case: start_time > end_time (e.g., 22:00 - 06:00)
            return now >= self.start_time or now <= self.end_time


@receiver(post_save, sender=SpendLog)
def update_brand_spend(sender: type[SpendLog], instance: SpendLog, created: bool, **kwargs: object) -> None:
    """Update brand's daily and monthly spend when a new spend log is created."""
    if created:
        brand = instance.campaign.brand
        brand.current_daily_spend += instance.amount
        brand.current_monthly_spend += instance.amount
        brand.save(update_fields=['current_daily_spend', 'current_monthly_spend'])
