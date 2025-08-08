from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from django.utils import timezone
from django.db.models import QuerySet, Sum
from .models import Brand, Campaign, SpendLog, DaypartingSchedule


class BudgetService:
    """Service class for budget-related operations."""
    
    @staticmethod
    def record_spend(campaign: Campaign, amount: Decimal, description: str = "") -> SpendLog:
        """
        Record a spend for a campaign and update brand totals.
        
        Args:
            campaign: The campaign to record spend for
            amount: The amount spent
            description: Optional description of the spend
            
        Returns:
            The created SpendLog instance
        """
        spend_log = SpendLog.objects.create(
            campaign=campaign,
            amount=amount,
            description=description
        )
        # Brand totals are updated via the post_save signal
        return spend_log
    
    @staticmethod
    def get_brand_summary(brand: Brand) -> Dict[str, object]:
        """
        Get a comprehensive summary of a brand's budget status.
        
        Args:
            brand: The brand to get summary for
            
        Returns:
            Dictionary containing budget summary information
        """
        return {
            'name': brand.name,
            'daily_budget': brand.daily_budget,
            'monthly_budget': brand.monthly_budget,
            'current_daily_spend': brand.current_daily_spend,
            'current_monthly_spend': brand.current_monthly_spend,
            'daily_remaining': brand.daily_budget_remaining,
            'monthly_remaining': brand.monthly_budget_remaining,
            'daily_exceeded': brand.is_daily_budget_exceeded,
            'monthly_exceeded': brand.is_monthly_budget_exceeded,
            'active_campaigns': brand.campaigns.filter(is_active=True).count(),
            'total_campaigns': brand.campaigns.count(),
        }
    
    @staticmethod
    def get_campaign_spend_today(campaign: Campaign) -> Decimal:
        """Get total spend for a campaign today."""
        today = timezone.now().date()
        total = SpendLog.objects.filter(
            campaign=campaign,
            timestamp__date=today
        ).aggregate(total=Sum('amount'))['total']
        
        return total or Decimal('0.00')


class DaypartingService:
    """Service class for dayparting-related operations."""
    
    @staticmethod
    def is_campaign_in_dayparting_window(campaign: Campaign) -> bool:
        """
        Check if a campaign is currently within its dayparting window.
        
        Args:
            campaign: The campaign to check
            
        Returns:
            True if campaign should be active based on dayparting, False otherwise
        """
        try:
            schedule = campaign.dayparting_schedule
            return schedule.is_active_now()
        except DaypartingSchedule.DoesNotExist:
            # If no dayparting schedule exists, campaign can run anytime
            return True
    
    @staticmethod
    def get_campaigns_for_dayparting_update() -> QuerySet[Campaign]:
        """
        Get campaigns that need dayparting status updates.
        
        Returns:
            QuerySet of campaigns with dayparting schedules
        """
        return Campaign.objects.filter(
            dayparting_schedule__isnull=False
        ).select_related('brand', 'dayparting_schedule')


class CampaignService:
    """Service class for campaign management operations."""
    
    @staticmethod
    def should_campaign_be_active(campaign: Campaign) -> Tuple[bool, List[str]]:
        """
        Determine if a campaign should be active based on all constraints.
        
        Args:
            campaign: The campaign to check
            
        Returns:
            Tuple of (should_be_active, list_of_blocking_reasons)
        """
        blocking_reasons: List[str] = []
        
        # Check budget constraints
        brand = campaign.brand
        if brand.is_daily_budget_exceeded:
            blocking_reasons.append("Daily budget exceeded")
        if brand.is_monthly_budget_exceeded:
            blocking_reasons.append("Monthly budget exceeded")
        
        # Check dayparting constraints
        if not DaypartingService.is_campaign_in_dayparting_window(campaign):
            blocking_reasons.append("Outside dayparting window")
        
        should_be_active = len(blocking_reasons) == 0
        return should_be_active, blocking_reasons
    
    @staticmethod
    def update_campaign_status(campaign: Campaign, force_update: bool = False) -> Tuple[bool, str]:
        """
        Update a campaign's status based on current constraints.
        
        Args:
            campaign: The campaign to update
            force_update: If True, update regardless of current status
            
        Returns:
            Tuple of (status_changed, reason_for_change)
        """
        should_be_active, blocking_reasons = CampaignService.should_campaign_be_active(campaign)
        
        if should_be_active == campaign.is_active and not force_update:
            return False, "No change needed"
        
        original_status = campaign.is_active
        campaign.is_active = should_be_active
        campaign.save(update_fields=['is_active'])
        
        if should_be_active and not original_status:
            return True, "Campaign activated (constraints cleared)"
        elif not should_be_active and original_status:
            return True, f"Campaign paused ({', '.join(blocking_reasons)})"
        else:
            return True, f"Status forced to {'active' if should_be_active else 'inactive'}"
    
    @staticmethod
    def get_campaign_performance_summary(campaign: Campaign) -> Dict[str, object]:
        """
        Get performance summary for a campaign.
        
        Args:
            campaign: The campaign to get summary for
            
        Returns:
            Dictionary containing campaign performance data
        """
        today_spend = BudgetService.get_campaign_spend_today(campaign)
        total_spend = SpendLog.objects.filter(campaign=campaign).aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        should_be_active, blocking_reasons = CampaignService.should_campaign_be_active(campaign)
        
        return {
            'name': campaign.name,
            'brand': campaign.brand.name,
            'is_active': campaign.is_active,
            'should_be_active': should_be_active,
            'blocking_reasons': blocking_reasons,
            'spend_today': today_spend,
            'total_spend': total_spend,
            'has_dayparting': hasattr(campaign, 'dayparting_schedule'),
            'in_dayparting_window': DaypartingService.is_campaign_in_dayparting_window(campaign),
        }
