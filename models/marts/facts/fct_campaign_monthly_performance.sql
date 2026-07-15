with
monthly_spend as (

    select
        c.*,
        date_trunc(a.date, month) as reporting_month,
        sum(a.cost) as spend,
        sum(a.impressions) as impressions,
        sum(a.clicks) as clicks,
        sum(a.clicks) / sum(a.impressions) as ctr,
        sum(a.cost) / sum(a.clicks) as monthly_cpc
    from {{ ref('campaigns') }} as c left join
        {{ ref('stg_paid_ads') }} as a
        on c.campaign_id = a.campaign_id
    group by all

),

monthly_leads as (

    select
        campaign_id,
        date_trunc(created_at, month) as created_month,
        count(distinct lead_id) as leads,
        count(distinct if(trial_start_at is not null, lead_id, null))
            as trials_unique,
        count(if(trial_start_at is not null, lead_id, null)) as trials_total,
        count(distinct if(close_status = 'Won', opportunity_id, null))
            as won_opportunities,
        sum(if(close_status = 'Won', amount, 0)) as closed_won_amount
    from {{ ref('stg_crm_pipeline') }}
    group by 1, 2

)

select
    monthly_spend.*,
    coalesce(monthly_leads.leads, 0) as leads,
    coalesce(monthly_leads.trials_unique, 0) as trials_unique,
    coalesce(monthly_leads.trials_total, 0) as trials_total,
    coalesce(monthly_leads.won_opportunities, 0) as won_opportunities,
    coalesce(monthly_leads.closed_won_amount, 0) as closed_won_amount,
    safe_divide(monthly_spend.spend, monthly_leads.leads) as cost_per_lead
from monthly_spend
left join monthly_leads
    on
        monthly_spend.campaign_id = monthly_leads.campaign_id
        and monthly_spend.reporting_month = monthly_leads.created_month
