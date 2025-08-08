from django.contrib import admin
from typing import Any
from django.db.models import QuerySet
from django.http import HttpRequest
from .models import Brand, Campaign, SpendLog, DaypartingSchedule


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'daily_budget', 'monthly_budget', 'current_daily_spend', 'current_monthly_spend')
    list_filter = ('daily_budget', 'monthly_budget')
    search_fields = ('name',)
    readonly_fields = ('current_daily_spend', 'current_monthly_spend')


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'is_active')
    list_filter = ('brand', 'is_active')
    search_fields = ('name', 'brand__name')


@admin.register(SpendLog)
class SpendLogAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'amount', 'timestamp')
    list_filter = ('campaign__brand', 'timestamp')
    search_fields = ('campaign__name', 'campaign__brand__name')
    readonly_fields = ('timestamp',)


@admin.register(DaypartingSchedule)
class DaypartingScheduleAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'start_time', 'end_time')
    list_filter = ('campaign__brand',)
    search_fields = ('campaign__name', 'campaign__brand__name')
