with source as (
    select * from {{ ref('product_usage_events') }}
)

select
    cast(event_time as timestamp) as event_time,
    company_id,
    user_id,
    event_type,
    plan_tier,
    cast(seats_used as int64) as seats_used
from source
