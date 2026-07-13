with source as (
    select * from {{ ref('crm_pipeline') }}
)

select
    lead_id,
    cast(created_at as date) as created_at,
    email_domain,
    company_id,
    company_name,
    campaign_id,
    utm_campaign,
    lifecycle_stage,
    opportunity_id,
    cast(opportunity_created_at as date) as opportunity_created_at,
    cast(amount as numeric) as amount,
    cast(close_date as date) as close_date,
    close_status,
    cast(trial_start_at as date) as trial_start_at,
    cast(trial_end_at as date) as trial_end_at
from source
