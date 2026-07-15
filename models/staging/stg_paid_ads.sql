with source as (
    select * from {{ ref('paid_ads') }}
)

select
    cast(date as date) as date,
    campaign_id,
    campaign_name,
    split(campaign_name, '_')[0] as region, 
    split(campaign_name, '_')[1] as feature, 
    split(campaign_name, '_')[2] as channel_from_name, 
    channel,
    utm_source,
    utm_medium,
    utm_campaign,
    cast(impressions as int64) as impressions,
    cast(clicks as int64) as clicks,
    cast(cost as numeric) as cost
from source
