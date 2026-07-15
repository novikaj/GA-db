{{ config(materialized='table') }}

WITH spine AS (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2024-12-01' as date)",
        end_date="cast(current_date() as date)"
    ) }}
)

SELECT
    DATE(date_day) AS cal_date,
    DATE_ADD(DATE(date_day), INTERVAL -1 DAY) AS d2,
    DATE_ADD(DATE(date_day), INTERVAL -6 DAY) AS d7,
    DATE_ADD(DATE(date_day), INTERVAL -29 DAY) AS d30,
    FORMAT_DATE('%A', DATE(date_day)) AS day_name
FROM spine
