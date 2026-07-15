with source as (
    select * from {{ ref('crm_pipeline') }}
)

select
    lead_id,
    created_at,
    email_domain,
    company_id,
    company_name,
    campaign_id,
    utm_campaign,
    lifecycle_stage,
    opportunity_id,
    opportunity_created_at,
    cast(amount as numeric) as amount,
    close_date,
    close_status,
    trial_start_at,
    trial_end_at
from source
