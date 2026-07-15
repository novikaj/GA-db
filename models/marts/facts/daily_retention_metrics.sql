with calendar_date as 
(select * from {{ ref('calendar_date') }}),

events as (
    select
        event_date,
        company_id,
        plan_tier,
        region,
        user_id,
        feature_x_events,
        feature_y_events,
        seat_added_events,
        invite_sent_events
    from {{ ref('daily_company_events') }}
    where trial_event = false
)

select
    cal_date,
    day_name,
    plan_tier,
    region,
    count(distinct case when event_date = cal_date then company_id end) as dac,
    count(
        distinct case
            when event_date between d2 and cal_date then company_id
        end
    ) as d2_companies,
    count(
        distinct case
            when event_date between d7 and cal_date then company_id
        end
    ) as wac,
    count(
        distinct case
            when event_date between d30 and cal_date then company_id
        end
    ) as mac,
    count(distinct case when event_date = cal_date then user_id end) as dau,
    count(
        distinct case when event_date between d2 and cal_date then user_id end
    ) as d2_users,
    count(
        distinct case when event_date between d7 and cal_date then user_id end
    ) as wau,
    count(
        distinct case when event_date between d30 and cal_date then user_id end
    ) as mau
from calendar_date
left join events on event_date between d30 and cal_date
where cal_date <= '2026-01-14'
group by all
