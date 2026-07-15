select distinct
    campaign_id,
    campaign_name,
    region,
    feature,
    channel_from_name,
    channel,
    utm_source,
    utm_medium,
    utm_campaign
from {{ ref('stg_paid_ads') }}
