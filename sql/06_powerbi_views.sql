-- 06_powerbi_views.sql: Pre-built Analytical Views for Power BI Import
-- Allows Power BI DirectQuery or Import mode to consume pre-aggregated star schema matrices directly.

DROP VIEW IF EXISTS vw_powerbi_funnel_conversion;
DROP VIEW IF EXISTS vw_powerbi_time_to_close;
DROP VIEW IF EXISTS vw_powerbi_seller_post_signing;
DROP VIEW IF EXISTS vw_powerbi_cohort_revenue;
DROP VIEW IF EXISTS vw_powerbi_channel_matrix;

-- View 1: Funnel Conversion by Origin & Cohort Month
CREATE VIEW vw_powerbi_funnel_conversion AS
SELECT 
    o.origin_name AS lead_origin,
    lp.landing_page_id,
    d.year,
    d.month,
    d.month_name,
    COUNT(f.lead_key) AS total_mqls,
    SUM(f.is_won) AS closed_deals,
    CAST(SUM(f.is_won) AS FLOAT) / COUNT(f.lead_key) AS conversion_rate
FROM fact_lead f
JOIN dim_origin o ON f.origin_key = o.origin_key
JOIN dim_landing_page lp ON f.landing_page_key = lp.landing_page_key
JOIN dim_date d ON f.date_key_first_contact = d.date_key
GROUP BY o.origin_name, lp.landing_page_id, d.year, d.month, d.month_name;

-- View 2: Time to Close Speed Metrics
CREATE VIEW vw_powerbi_time_to_close AS
SELECT 
    o.origin_name AS lead_origin,
    seg.segment_name AS business_segment,
    f.mql_id,
    f.days_to_close,
    f.is_won
FROM fact_lead f
JOIN dim_origin o ON f.origin_key = o.origin_key
JOIN dim_segment seg ON f.segment_key = seg.segment_key;

-- View 3: Seller Post-Signing Performance
CREATE VIEW vw_powerbi_seller_post_signing AS
SELECT 
    sel.seller_id,
    sel.seller_key,
    o.origin_name AS lead_origin,
    seg.segment_name AS business_segment,
    sel.lead_type,
    sel.lead_behaviour_profile,
    sel.declared_monthly_revenue,
    COUNT(DISTINCT foi.order_id) AS total_orders,
    SUM(foi.price) AS total_revenue,
    SUM(foi.freight_value) AS total_freight,
    AVG(foi.review_score) AS avg_review_score,
    MIN(foi.days_after_won) AS days_to_first_order
FROM dim_seller sel
JOIN fact_lead fl ON sel.seller_key = fl.seller_key OR sel.seller_id = fl.mql_id
JOIN dim_origin o ON fl.origin_key = o.origin_key
JOIN dim_segment seg ON fl.segment_key = seg.segment_key
LEFT JOIN fact_order_item foi ON sel.seller_key = foi.seller_key AND foi.days_after_won >= 0
GROUP BY sel.seller_id, sel.seller_key, o.origin_name, seg.segment_name, sel.lead_type, sel.lead_behaviour_profile, sel.declared_monthly_revenue;

-- View 4: Cohort Revenue Matrix
CREATE VIEW vw_powerbi_cohort_revenue AS
SELECT 
    o.origin_name AS lead_origin,
    CAST(foi.days_after_won / 30 AS INTEGER) AS months_since_signing,
    COUNT(DISTINCT foi.seller_key) AS active_sellers,
    SUM(foi.price) AS monthly_revenue
FROM fact_order_item foi
JOIN dim_seller sel ON foi.seller_key = sel.seller_key
JOIN fact_lead fl ON sel.seller_key = fl.seller_key OR sel.seller_id = fl.mql_id
JOIN dim_origin o ON fl.origin_key = o.origin_key
WHERE foi.days_after_won >= 0 AND foi.order_status != 'canceled'
GROUP BY o.origin_name, CAST(foi.days_after_won / 30 AS INTEGER);

-- View 5: Master Channel Efficiency Matrix
CREATE VIEW vw_powerbi_channel_matrix AS
WITH mql_stats AS (
    SELECT 
        o.origin_name AS lead_origin,
        COUNT(fl.lead_key) AS total_mqls,
        SUM(fl.is_won) AS closed_deals,
        AVG(CASE WHEN fl.is_won = 1 THEN fl.days_to_close END) AS avg_days_to_close
    FROM fact_lead fl
    JOIN dim_origin o ON fl.origin_key = o.origin_key
    GROUP BY o.origin_name
),
rev_stats AS (
    SELECT 
        o.origin_name AS lead_origin,
        COUNT(DISTINCT foi.seller_key) AS active_sellers,
        COUNT(DISTINCT foi.order_id) AS total_orders,
        SUM(foi.price) AS total_post_signing_revenue,
        AVG(foi.review_score) AS avg_review_score
    FROM fact_order_item foi
    JOIN dim_seller sel ON foi.seller_key = sel.seller_key
    JOIN fact_lead fl ON sel.seller_key = fl.seller_key OR sel.seller_id = fl.mql_id
    JOIN dim_origin o ON fl.origin_key = o.origin_key
    WHERE foi.days_after_won >= 0 AND foi.order_status != 'canceled'
    GROUP BY o.origin_name
)
SELECT 
    m.lead_origin,
    m.total_mqls,
    m.closed_deals,
    CAST(m.closed_deals AS FLOAT) / m.total_mqls AS conversion_rate,
    m.avg_days_to_close,
    COALESCE(r.active_sellers, 0) AS active_sellers,
    CAST(COALESCE(r.active_sellers, 0) AS FLOAT) / NULLIF(m.closed_deals, 0) AS activation_rate,
    COALESCE(r.total_orders, 0) AS total_orders,
    COALESCE(r.total_post_signing_revenue, 0.0) AS total_post_signing_revenue,
    COALESCE(r.total_post_signing_revenue, 0.0) / NULLIF(m.closed_deals, 0) AS revenue_per_closed_deal,
    COALESCE(r.avg_review_score, 0.0) AS avg_review_score
FROM mql_stats m
LEFT JOIN rev_stats r ON m.lead_origin = r.lead_origin;
