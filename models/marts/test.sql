select
  company_id,
  count(*) as crm_rows,
  count(distinct campaign_id) as campaigns,
  count(distinct trial_start_at) as trial_periods
from {{ ref('stg_crm_pipeline') }}
group by 1
having count(*) > 1