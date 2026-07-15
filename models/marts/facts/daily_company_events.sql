with high_level_info as (

    select
        e.*,
        p.lifecycle_stage,
        p.trial_start_at,
        p.trial_end_at,
        c.region,
        c.feature as feature_marketed,
        c.channel,
        c.channel_from_name,

        coalesce(date(
            e.event_time
        ) between p.trial_start_at and p.trial_end_at,
        false) as trial_event,

        case
            when date(e.event_time) between p.trial_start_at and p.trial_end_at
                then concat(e.plan_tier, ' trial')
            else e.plan_tier
        end as full_tier

    from {{ ref('stg_product_usage_events') }} as e
    left join {{ ref('stg_crm_pipeline') }} as p
        on e.company_id = p.company_id
    left join {{ ref('campaigns') }} as c on p.campaign_id = c.campaign_id

)

select
    company_id,
    lifecycle_stage,
    trial_start_at,
    trial_end_at,
    trial_event,
    plan_tier,
    full_tier,
    region,
    feature_marketed,
    channel,
    channel_from_name,
    user_id,
    date(event_time) as event_date,
    avg(seats_used) as avg_daily_seats,
    sum(distinct case when event_type = 'login' then 1 else 0 end)
        as login_users,
    sum(case when event_type = 'feature_x_used' then 1 else 0 end)
        as feature_x_events,
    sum(case when event_type = 'feature_y_used' then 1 else 0 end)
        as feature_y_events,
    sum(case when event_type = 'seat_added' then 1 else 0 end)
        as seat_added_events,
    sum(case when event_type = 'invite_sent' then 1 else 0 end)
        as invite_sent_events

from high_level_info
group by all
