# Pseudocode Documentation
## Django + Celery Budget Management System

### Data Models

```
Brand:
  - id (primary key)
  - name (unique string)
  - daily_budget (decimal)
  - monthly_budget (decimal)
  - current_daily_spend (decimal, default 0)
  - current_monthly_spend (decimal, default 0)
  - created_at, updated_at (timestamps)
  
  Properties:
    - daily_budget_remaining = daily_budget - current_daily_spend
    - monthly_budget_remaining = monthly_budget - current_monthly_spend
    - is_daily_budget_exceeded = current_daily_spend >= daily_budget
    - is_monthly_budget_exceeded = current_monthly_spend >= monthly_budget

Campaign:
  - id (primary key)
  - name (string)
  - brand (foreign key to Brand)
  - is_active (boolean, default true)
  - created_at, updated_at (timestamps)
  
  Properties:
    - total_spend_today = sum of SpendLog amounts for today

SpendLog:
  - id (primary key)
  - campaign (foreign key to Campaign)
  - amount (decimal)
  - timestamp (auto-generated)
  - description (optional text)

DaypartingSchedule:
  - id (primary key)
  - campaign (one-to-one with Campaign)
  - start_time (time)
  - end_time (time)
  - timezone (string, default UTC)
  
  Methods:
    - is_active_now() -> boolean:
        current_time = get_current_time()
        if start_time <= end_time:
            return start_time <= current_time <= end_time
        else:  // overnight case (e.g., 22:00 - 06:00)
            return current_time >= start_time OR current_time <= end_time
```

### Core Business Logic

#### 1. Spend Tracking
```
FUNCTION record_spend(campaign, amount, description=""):
    spend_log = CREATE SpendLog(campaign, amount, description)
    brand = campaign.brand
    brand.current_daily_spend += amount
    brand.current_monthly_spend += amount
    brand.save()
    RETURN spend_log
```

#### 2. Budget Enforcement
```
FUNCTION enforce_budgets():
    paused_campaigns = []
    
    FOR EACH brand IN all_brands:
        IF brand.is_daily_budget_exceeded OR brand.is_monthly_budget_exceeded:
            active_campaigns = GET campaigns WHERE brand=brand AND is_active=true
            FOR EACH campaign IN active_campaigns:
                campaign.is_active = false
                campaign.save()
                paused_campaigns.APPEND(campaign)
    
    RETURN summary_of_paused_campaigns
```

#### 3. Dayparting Enforcement
```
FUNCTION enforce_dayparting():
    activated_campaigns = []
    deactivated_campaigns = []
    
    FOR EACH schedule IN all_dayparting_schedules:
        campaign = schedule.campaign
        should_be_active = schedule.is_active_now()
        
        IF should_be_active AND NOT campaign.is_active:
            // Only activate if brand has budget
            IF NOT campaign.brand.is_daily_budget_exceeded AND NOT campaign.brand.is_monthly_budget_exceeded:
                campaign.is_active = true
                campaign.save()
                activated_campaigns.APPEND(campaign)
        
        ELSE IF NOT should_be_active AND campaign.is_active:
            campaign.is_active = false
            campaign.save()
            deactivated_campaigns.APPEND(campaign)
    
    RETURN summary_of_changes
```

#### 4. Daily/Monthly Resets
```
FUNCTION reset_daily_monthly_spends():
    today = get_current_date()
    reactivated_campaigns = []
    
    FOR EACH brand IN all_brands:
        brand.current_daily_spend = 0
        
        IF today.day == 1:  // First day of month
            brand.current_monthly_spend = 0
        
        brand.save()
    
    // Reactivate eligible campaigns
    FOR EACH campaign IN inactive_campaigns:
        IF campaign_should_be_active(campaign):
            campaign.is_active = true
            campaign.save()
            reactivated_campaigns.APPEND(campaign)
    
    RETURN summary_of_resets_and_reactivations

FUNCTION campaign_should_be_active(campaign):
    brand = campaign.brand
    
    // Check budget constraints
    IF brand.is_daily_budget_exceeded OR brand.is_monthly_budget_exceeded:
        RETURN false
    
    // Check dayparting constraints
    IF campaign.has_dayparting_schedule:
        IF NOT campaign.dayparting_schedule.is_active_now():
            RETURN false
    
    RETURN true
```

### Celery Task Schedule

```
PERIODIC_TASKS:
  - enforce_budgets: runs every 5 minutes
  - enforce_dayparting: runs every 1 minute
  - reset_daily_monthly_spends: runs daily at midnight (00:00)
  - check_and_update_campaign_status: comprehensive check, runs every 2 minutes
```

### System Workflow

#### Daily Workflow:
1. **Midnight (00:00)**: Reset daily spends, reset monthly spends (if 1st of month)
2. **Continuous**: Record spend logs as they occur
3. **Every minute**: Check dayparting windows, activate/deactivate campaigns
4. **Every 5 minutes**: Check budget constraints, pause overspending campaigns
5. **Real-time**: Spend logs automatically update brand totals via database signals

#### Monthly Workflow:
1. **1st of month at midnight**: Reset monthly spends for all brands
2. **1st of month**: Reactivate campaigns that were paused due to monthly budget limits

### Key Assumptions:
1. Campaigns are automatically reactivated when constraints are cleared
2. Budget checks take priority over dayparting (budget exceeded = always paused)
3. Spend logs immediately update brand totals
4. Each campaign can have at most one dayparting schedule
5. Times are handled in UTC unless specified otherwise
6. Decimal precision is used for financial calculations
7. Campaign status changes are logged and auditable
