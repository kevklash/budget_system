from celery import shared_task
from django.utils import timezone
from django.db.models import QuerySet
from typing import List
from decimal import Decimal
from .models import Brand, Campaign, DaypartingSchedule


@shared_task
def enforce_budgets() -> str:
    """
    Check all brands and pause campaigns if budgets are exceeded.
    Returns a summary of actions taken.
    """
    paused_campaigns: List[str] = []
    
    brands: QuerySet[Brand] = Brand.objects.all()
    for brand in brands:
        if brand.is_daily_budget_exceeded or brand.is_monthly_budget_exceeded:
            active_campaigns: QuerySet[Campaign] = Campaign.objects.filter(
                brand=brand, 
                is_active=True
            )
            
            for campaign in active_campaigns:
                campaign.is_active = False
                campaign.save(update_fields=['is_active'])
                paused_campaigns.append(f"{campaign.name} ({brand.name})")
    
    return f"Paused {len(paused_campaigns)} campaigns: {', '.join(paused_campaigns)}" if paused_campaigns else "No campaigns paused"


@shared_task
def enforce_dayparting() -> str:
    """
    Check dayparting schedules and enable/disable campaigns based on current time.
    Returns a summary of actions taken.
    """
    activated_campaigns: List[str] = []
    deactivated_campaigns: List[str] = []
    
    schedules: QuerySet[DaypartingSchedule] = DaypartingSchedule.objects.select_related('campaign', 'campaign__brand')
    
    for schedule in schedules:
        campaign = schedule.campaign
        should_be_active = schedule.is_active_now()
        
        # Only change status if within budget limits
        if should_be_active and not campaign.is_active:
            # Check if brand has budget remaining
            brand = campaign.brand
            if not brand.is_daily_budget_exceeded and not brand.is_monthly_budget_exceeded:
                campaign.is_active = True
                campaign.save(update_fields=['is_active'])
                activated_campaigns.append(f"{campaign.name} ({brand.name})")
        elif not should_be_active and campaign.is_active:
            campaign.is_active = False
            campaign.save(update_fields=['is_active'])
            deactivated_campaigns.append(f"{campaign.name} ({brand.name})")
    
    result_parts = []
    if activated_campaigns:
        result_parts.append(f"Activated {len(activated_campaigns)} campaigns: {', '.join(activated_campaigns)}")
    if deactivated_campaigns:
        result_parts.append(f"Deactivated {len(deactivated_campaigns)} campaigns: {', '.join(deactivated_campaigns)}")
    
    return "; ".join(result_parts) if result_parts else "No dayparting changes made"


@shared_task
def reset_daily_monthly_spends() -> str:
    """
    Reset daily spends for all brands. Reset monthly spends on the 1st of each month.
    Reactivate eligible campaigns.
    Returns a summary of actions taken.
    """
    today = timezone.now().date()
    brands: QuerySet[Brand] = Brand.objects.all()
    reactivated_campaigns: List[str] = []
    
    # Reset daily spends for all brands
    for brand in brands:
        brand.current_daily_spend = Decimal('0.00')
        
        # Reset monthly spend if it's the first day of the month
        if today.day == 1:
            brand.current_monthly_spend = Decimal('0.00')
        
        brand.save(update_fields=['current_daily_spend', 'current_monthly_spend'])
    
    # Reactivate campaigns that are within budget and dayparting windows
    inactive_campaigns: QuerySet[Campaign] = Campaign.objects.filter(is_active=False).select_related('brand')
    
    for campaign in inactive_campaigns:
        brand = campaign.brand
        
        # Check budget constraints
        if brand.is_daily_budget_exceeded or brand.is_monthly_budget_exceeded:
            continue
            
        # Check dayparting constraints if exists
        if hasattr(campaign, 'dayparting_schedule'):
            if not campaign.dayparting_schedule.is_active_now():
                continue
        
        # Reactivate the campaign
        campaign.is_active = True
        campaign.save(update_fields=['is_active'])
        reactivated_campaigns.append(f"{campaign.name} ({brand.name})")
    
    summary_parts = [f"Reset daily spends for {brands.count()} brands"]
    
    if today.day == 1:
        summary_parts.append(f"Reset monthly spends for {brands.count()} brands")
    
    if reactivated_campaigns:
        summary_parts.append(f"Reactivated {len(reactivated_campaigns)} campaigns: {', '.join(reactivated_campaigns)}")
    
    return "; ".join(summary_parts)


@shared_task
def check_and_update_campaign_status() -> str:
    """
    Comprehensive task that checks both budget and dayparting constraints.
    This can be run more frequently for real-time enforcement.
    """
    budget_result = enforce_budgets()
    dayparting_result = enforce_dayparting()
    
    return f"Budget check: {budget_result}; Dayparting check: {dayparting_result}"
