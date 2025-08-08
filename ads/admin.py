from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from typing import Any
from decimal import Decimal
from django.db.models import QuerySet
from django.http import HttpRequest
from .models import Brand, Campaign, SpendLog, DaypartingSchedule


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'daily_budget', 
        'current_daily_spend', 
        'daily_budget_status',
        'monthly_budget', 
        'current_monthly_spend', 
        'monthly_budget_status'
    )
    list_filter = ('daily_budget', 'monthly_budget')
    search_fields = ('name',)
    readonly_fields = (
        'current_daily_spend', 
        'current_monthly_spend', 
        'daily_budget_remaining',
        'monthly_budget_remaining',
        'daily_budget_percentage_used',
        'monthly_budget_percentage_used'
    )
    
    def daily_budget_status(self, obj):
        """Show daily budget status with color coding"""
        remaining = float(obj.daily_budget_remaining)
        percentage = (float(obj.current_daily_spend) / float(obj.daily_budget) * 100) if obj.daily_budget > 0 else 0
        
        if remaining <= 0:
            color = 'red'
            status = 'EXCEEDED'
        elif percentage >= 90:
            color = 'orange'
            status = 'WARNING'
        elif percentage >= 75:
            color = 'yellow'
            status = 'CAUTION'
        else:
            color = 'green'
            status = 'OK'
            
        return format_html(
            '<span style="color: {}; font-weight: bold;">${} ({})</span>',
            color, f'{remaining:.2f}', status
        )
    daily_budget_status.short_description = 'Daily Remaining'
    
    def monthly_budget_status(self, obj):
        """Show monthly budget status with color coding"""
        remaining = float(obj.monthly_budget_remaining)
        percentage = (float(obj.current_monthly_spend) / float(obj.monthly_budget) * 100) if obj.monthly_budget > 0 else 0
        
        if remaining <= 0:
            color = 'red'
            status = 'EXCEEDED'
        elif percentage >= 90:
            color = 'orange'
            status = 'WARNING'
        elif percentage >= 75:
            color = 'yellow'
            status = 'CAUTION'
        else:
            color = 'green'
            status = 'OK'
            
        return format_html(
            '<span style="color: {}; font-weight: bold;">${} ({})</span>',
            color, f'{remaining:.2f}', status
        )
    monthly_budget_status.short_description = 'Monthly Remaining'
    
    def daily_budget_remaining(self, obj):
        """Show remaining daily budget"""
        remaining = float(obj.daily_budget_remaining)
        return f"${remaining:.2f}"
    daily_budget_remaining.short_description = 'Daily Remaining'
    
    def monthly_budget_remaining(self, obj):
        """Show remaining monthly budget"""
        remaining = float(obj.monthly_budget_remaining)
        return f"${remaining:.2f}"
    monthly_budget_remaining.short_description = 'Monthly Remaining'
    
    def daily_budget_percentage_used(self, obj):
        """Show percentage of daily budget used"""
        if obj.daily_budget > 0:
            percentage = (float(obj.current_daily_spend) / float(obj.daily_budget) * 100)
            return f"{percentage:.1f}%"
        return "0%"
    daily_budget_percentage_used.short_description = 'Daily % Used'
    
    def monthly_budget_percentage_used(self, obj):
        """Show percentage of monthly budget used"""
        if obj.monthly_budget > 0:
            percentage = (float(obj.current_monthly_spend) / float(obj.monthly_budget) * 100)
            return f"{percentage:.1f}%"
        return "0%"
    monthly_budget_percentage_used.short_description = 'Monthly % Used'


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'brand', 
        'is_active', 
        'brand_daily_remaining',
        'brand_monthly_remaining',
        'total_spend_today',
        'campaign_status'
    )
    list_filter = ('brand', 'is_active')
    search_fields = ('name', 'brand__name')
    readonly_fields = (
        'total_spend_today',
        'brand_daily_budget_status',
        'brand_monthly_budget_status',
    )
    
    def brand_daily_remaining(self, obj):
        """Show brand's remaining daily budget"""
        remaining = float(obj.brand.daily_budget_remaining)
        daily_budget = float(obj.brand.daily_budget)
        if remaining <= 0:
            return format_html('<span style="color: red; font-weight: bold;">${}</span>', f'{remaining:.2f}')
        elif remaining < daily_budget * 0.2:  # Less than 20% remaining
            return format_html('<span style="color: orange; font-weight: bold;">${}</span>', f'{remaining:.2f}')
        else:
            return format_html('<span style="color: green;">${}</span>', f'{remaining:.2f}')
    brand_daily_remaining.short_description = 'Daily Budget Left'
    
    def brand_monthly_remaining(self, obj):
        """Show brand's remaining monthly budget"""
        remaining = float(obj.brand.monthly_budget_remaining)
        monthly_budget = float(obj.brand.monthly_budget)
        if remaining <= 0:
            return format_html('<span style="color: red; font-weight: bold;">${}</span>', f'{remaining:.2f}')
        elif remaining < monthly_budget * 0.2:  # Less than 20% remaining
            return format_html('<span style="color: orange; font-weight: bold;">${}</span>', f'{remaining:.2f}')
        else:
            return format_html('<span style="color: green;">${}</span>', f'{remaining:.2f}')
    brand_monthly_remaining.short_description = 'Monthly Budget Left'
    
    def total_spend_today(self, obj):
        """Show campaign's spend for today"""
        today_spend = float(obj.total_spend_today)
        return f"${today_spend:.2f}"
    total_spend_today.short_description = "Today's Spend"
    
    def campaign_status(self, obj):
        """Show overall campaign status"""
        if not obj.is_active:
            return format_html('<span style="color: red; font-weight: bold;">INACTIVE</span>')
        
        brand = obj.brand
        if brand.is_daily_budget_exceeded:
            return format_html('<span style="color: red; font-weight: bold;">DAILY EXCEEDED</span>')
        elif brand.is_monthly_budget_exceeded:
            return format_html('<span style="color: red; font-weight: bold;">MONTHLY EXCEEDED</span>')
        else:
            return format_html('<span style="color: green; font-weight: bold;">ACTIVE</span>')
    campaign_status.short_description = 'Status'
    
    def brand_daily_budget_status(self, obj):
        """Detailed daily budget status for detail view"""
        brand = obj.brand
        current_spend = float(brand.current_daily_spend)
        daily_budget = float(brand.daily_budget)
        percentage = (current_spend / daily_budget * 100) if daily_budget > 0 else 0
        return f"${current_spend:.2f} of ${daily_budget:.2f} ({percentage:.1f}% used)"
    brand_daily_budget_status.short_description = 'Brand Daily Budget Status'
    
    def brand_monthly_budget_status(self, obj):
        """Detailed monthly budget status for detail view"""
        brand = obj.brand
        current_spend = float(brand.current_monthly_spend)
        monthly_budget = float(brand.monthly_budget)
        percentage = (current_spend / monthly_budget * 100) if monthly_budget > 0 else 0
        return f"${current_spend:.2f} of ${monthly_budget:.2f} ({percentage:.1f}% used)"
    brand_monthly_budget_status.short_description = 'Brand Monthly Budget Status'


@admin.register(SpendLog)
class SpendLogAdmin(admin.ModelAdmin):
    list_display = (
        'campaign', 
        'brand_name',
        'amount', 
        'timestamp',
        'running_daily_total',
        'running_monthly_total'
    )
    list_filter = ('campaign__brand', 'timestamp')
    search_fields = ('campaign__name', 'campaign__brand__name', 'description')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    def brand_name(self, obj):
        """Show the brand name for easy reference"""
        return obj.campaign.brand.name
    brand_name.short_description = 'Brand'
    
    def running_daily_total(self, obj):
        """Show brand's current daily spend"""
        daily_spend = float(obj.campaign.brand.current_daily_spend)
        return f"${daily_spend:.2f}"
    running_daily_total.short_description = 'Brand Daily Total'
    
    def running_monthly_total(self, obj):
        """Show brand's current monthly spend"""
        monthly_spend = float(obj.campaign.brand.current_monthly_spend)
        return f"${monthly_spend:.2f}"
    running_monthly_total.short_description = 'Brand Monthly Total'


@admin.register(DaypartingSchedule)
class DaypartingScheduleAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'start_time', 'end_time')
    list_filter = ('campaign__brand',)
    search_fields = ('campaign__name', 'campaign__brand__name')
