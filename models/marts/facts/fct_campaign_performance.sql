with ad_spend as (
    select
        campaign_id,
        any_value(campaign_name) as campaign_name,
        any_value(channel) as channel,
        sum(impressions) as impressions,
        sum(clicks) as clicks,
        sum(cost) as spend
    from {{ ref('stg_paid_ads') }}
    group by 1
),

crm as (
    select
        campaign_id,
        count(distinct lead_id) as leads,
        count(distinct if(lifecycle_stage = 'Trial', lead_id, null)) as trials,
        count(distinct if(close_status = 'Won', opportunity_id, null)) as won_opportunities,
        sum(if(close_status = 'Won', amount, 0)) as closed_won_amount
    from {{ ref('stg_crm_pipeline') }}
    group by 1
)

select
    ad_spend.campaign_id,
    ad_spend.campaign_name,
    ad_spend.channel,
    ad_spend.impressions,
    ad_spend.clicks,
    ad_spend.spend,
    coalesce(crm.leads, 0) as leads,
    coalesce(crm.trials, 0) as trials,
    coalesce(crm.won_opportunities, 0) as won_opportunities,
    coalesce(crm.closed_won_amount, 0) as closed_won_amount,
    safe_divide(ad_spend.spend, nullif(ad_spend.clicks, 0)) as cost_per_click,
    safe_divide(ad_spend.spend, nullif(crm.leads, 0)) as cost_per_lead,
    safe_divide(crm.closed_won_amount, nullif(ad_spend.spend, 0)) as roas
from ad_spend
left join crm using (campaign_id)
