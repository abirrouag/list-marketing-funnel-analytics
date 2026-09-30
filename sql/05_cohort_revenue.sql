-- 05_cohort_revenue.sql: Cohort Revenue & Monthly Activation Trajectory
-- Answers: How rapidly do signed sellers ramp up sales month-by-month, and what is the cumulative revenue trajectory by acquisition channel?

WITH seller_first_order AS (
    SELECT 
        foi.seller_key,
        MIN(foi.days_after_won) AS days_to_first_order
    FROM fact_order_item foi
    WHERE foi.days_after_won >= 0 AND foi.order_status != 'canceled'
    GROUP BY foi.seller_key
),
seller_monthly_revenue AS (
    SELECT 
        o.origin_name AS lead_origin,
        sel.seller_key,
        CAST(foi.days_after_won / 30 AS INTEGER) AS months_since_signing,
        SUM(foi.price) AS monthly_revenue
    FROM fact_order_item foi
    JOIN dim_seller sel ON foi.seller_key = sel.seller_key
    JOIN fact_lead fl ON sel.seller_key = fl.seller_key OR sel.seller_id = fl.mql_id
    JOIN dim_origin o ON fl.origin_key = o.origin_key
    WHERE foi.days_after_won >= 0 AND foi.order_status != 'canceled'
    GROUP BY o.origin_name, sel.seller_key, CAST(foi.days_after_won / 30 AS INTEGER)
),
cohort_summary AS (
    SELECT 
        lead_origin,
        months_since_signing,
        COUNT(DISTINCT seller_key) AS active_sellers_in_month,
        SUM(monthly_revenue) AS cohort_monthly_revenue
    FROM seller_monthly_revenue
    WHERE months_since_signing BETWEEN 0 AND 12
    GROUP BY lead_origin, months_since_signing
)
SELECT 
    lead_origin,
    months_since_signing,
    active_sellers_in_month,
    ROUND(cohort_monthly_revenue, 2) AS monthly_revenue,
    ROUND(SUM(cohort_monthly_revenue) OVER (
        PARTITION BY lead_origin 
        ORDER BY months_since_signing 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ), 2) AS cumulative_cohort_revenue
FROM cohort_summary
ORDER BY lead_origin, months_since_signing;
