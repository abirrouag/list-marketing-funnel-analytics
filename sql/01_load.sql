-- 01_load.sql: Data Warehousing Load Script (Staging -> Dims & Facts)
-- Answers: How raw CSV data is cleansed, mapped with surrogate keys, and loaded into Star Schema tables.

-- 1. Load Dimension: dim_origin (Handling NULL origin as 'unknown')
INSERT INTO dim_origin (origin_key, origin_name)
SELECT 
    ROW_NUMBER() OVER (ORDER BY origin_name) AS origin_key,
    origin_name
FROM (
    SELECT DISTINCT LOWER(COALESCE(origin, 'unknown')) AS origin_name
    FROM staging_mql
) s;

-- 2. Load Dimension: dim_seller
INSERT INTO dim_seller (
    seller_key, seller_id, won_date, lead_type, lead_behaviour_profile, 
    business_type, declared_monthly_revenue, declared_product_catalog_size, 
    average_stock, has_company, has_gtin, city, state
)
SELECT 
    ROW_NUMBER() OVER (ORDER BY s.seller_id) AS seller_key,
    s.seller_id,
    c.won_date,
    COALESCE(c.lead_type, 'unknown'),
    COALESCE(c.lead_behaviour_profile, 'unknown'),
    COALESCE(c.business_type, 'unknown'),
    COALESCE(c.declared_monthly_revenue, 0.0),
    COALESCE(c.declared_product_catalog_size, 0),
    COALESCE(c.average_stock, 'unknown'),
    COALESCE(c.has_company, 0),
    COALESCE(c.has_gtin, 0),
    s.seller_city,
    s.seller_state
FROM staging_sellers s
LEFT JOIN staging_closed_deals c ON s.seller_id = c.seller_id;

-- 3. Load Fact Table: fact_lead
INSERT INTO fact_lead (
    lead_key, mql_id, date_key_first_contact, origin_key, landing_page_key,
    is_won, date_key_won, days_to_close, seller_key, segment_key, sdr_key, sr_key
)
SELECT 
    ROW_NUMBER() OVER (ORDER BY m.mql_id) AS lead_key,
    m.mql_id,
    CAST(STRFTIME('%Y%m%d', m.first_contact_date) AS INTEGER) AS date_key_first_contact,
    o.origin_key,
    lp.landing_page_key,
    CASE WHEN c.seller_id IS NOT NULL THEN 1 ELSE 0 END AS is_won,
    CASE WHEN c.won_date IS NOT NULL THEN CAST(STRFTIME('%Y%m%d', c.won_date) AS INTEGER) ELSE NULL END AS date_key_won,
    CASE WHEN c.won_date IS NOT NULL THEN CAST(JULIANDAY(c.won_date) - JULIANDAY(m.first_contact_date) AS INTEGER) ELSE NULL END AS days_to_close,
    sel.seller_key,
    seg.segment_key,
    sdr.sdr_key,
    sr.sr_key
FROM staging_mql m
LEFT JOIN staging_closed_deals c ON m.mql_id = c.mql_id
JOIN dim_origin o ON LOWER(COALESCE(m.origin, 'unknown')) = o.origin_name
JOIN dim_landing_page lp ON m.landing_page_id = lp.landing_page_id
LEFT JOIN dim_seller sel ON c.seller_id = sel.seller_id
LEFT JOIN dim_segment seg ON LOWER(COALESCE(c.business_segment, 'unknown')) = seg.segment_name
LEFT JOIN dim_sdr sdr ON c.sdr_id = sdr.sdr_id
LEFT JOIN dim_sr sr ON c.sr_id = sr.sr_id;
