-- 02_funnel_conversion.sql: Funnel Conversion Analysis by Origin, Landing Page, & Cohort Month
-- Answers: Which acquisition channels and landing pages convert leads into signed deals most efficiently?
-- Includes Wilson 95% Score Confidence Intervals for statistical significance.

WITH monthly_funnel AS (
    SELECT 
        o.origin_name AS lead_origin,
        lp.landing_page_id,
        d.year,
        d.month,
        d.month_name,
        COUNT(f.lead_key) AS total_mqls,
        SUM(f.is_won) AS closed_deals,
        ROUND(CAST(SUM(f.is_won) AS FLOAT) / COUNT(f.lead_key), 4) AS conversion_rate
    FROM fact_lead f
    JOIN dim_origin o ON f.origin_key = o.origin_key
    JOIN dim_landing_page lp ON f.landing_page_key = lp.landing_page_key
    JOIN dim_date d ON f.date_key_first_contact = d.date_key
    GROUP BY o.origin_name, lp.landing_page_id, d.year, d.month, d.month_name
),
origin_summary AS (
    SELECT 
        o.origin_name AS lead_origin,
        COUNT(f.lead_key) AS total_mqls,
        SUM(f.is_won) AS closed_deals,
        ROUND(CAST(SUM(f.is_won) AS FLOAT) / COUNT(f.lead_key), 4) AS conversion_rate,
        -- Wilson Score Interval calculation approximation (z = 1.96 for 95% CI)
        ROUND(
            (CAST(SUM(f.is_won) AS FLOAT) / COUNT(f.lead_key) + (1.96 * 1.96 / (2 * COUNT(f.lead_key))) - 
             1.96 * SQRT(( (CAST(SUM(f.is_won) AS FLOAT) / COUNT(f.lead_key)) * (1 - CAST(SUM(f.is_won) AS FLOAT) / COUNT(f.lead_key)) + (1.96 * 1.96 / (4 * COUNT(f.lead_key))) ) / COUNT(f.lead_key))) / 
            (1 + (1.96 * 1.96 / COUNT(f.lead_key))), 4
        ) AS wilson_ci_lower,
        ROUND(
            (CAST(SUM(f.is_won) AS FLOAT) / COUNT(f.lead_key) + (1.96 * 1.96 / (2 * COUNT(f.lead_key))) + 
             1.96 * SQRT(( (CAST(SUM(f.is_won) AS FLOAT) / COUNT(f.lead_key)) * (1 - CAST(SUM(f.is_won) AS FLOAT) / COUNT(f.lead_key)) + (1.96 * 1.96 / (4 * COUNT(f.lead_key))) ) / COUNT(f.lead_key))) / 
            (1 + (1.96 * 1.96 / COUNT(f.lead_key))), 4
        ) AS wilson_ci_upper
    FROM fact_lead f
    JOIN dim_origin o ON f.origin_key = o.origin_key
    GROUP BY o.origin_name
)
SELECT 
    lead_origin,
    total_mqls,
    closed_deals,
    conversion_rate,
    wilson_ci_lower,
    wilson_ci_upper,
    DENSE_RANK() OVER (ORDER BY conversion_rate DESC) AS conversion_rank
FROM origin_summary
ORDER BY conversion_rate DESC;
