-- 03_time_to_close.sql: Time-to-Close Speed Analysis by Origin & Business Segment
-- Answers: How long does it take for leads to convert from first contact to won seller?
-- Note: Analyzes closed deals only (days_to_close IS NOT NULL).
-- Open/unwon leads represent right-censored data, which is modeled statistically via Kaplan-Meier curves in Python.

-- Time-to-close distribution by Lead Origin
WITH ordered_leads_origin AS (
    SELECT 
        o.origin_name AS lead_origin,
        f.days_to_close,
        ROW_NUMBER() OVER (PARTITION BY o.origin_name ORDER BY f.days_to_close) AS row_num,
        COUNT(*) OVER (PARTITION BY o.origin_name) AS total_closed
    FROM fact_lead f
    JOIN dim_origin o ON f.origin_key = o.origin_key
    WHERE f.is_won = 1 AND f.days_to_close IS NOT NULL
)
SELECT 
    lead_origin,
    total_closed,
    MIN(days_to_close) AS min_days,
    MAX(CASE WHEN row_num = CAST(ROUND(0.50 * total_closed) AS INTEGER) THEN days_to_close END) AS median_days_to_close,
    MAX(CASE WHEN row_num = CAST(ROUND(0.75 * total_closed) AS INTEGER) THEN days_to_close END) AS p75_days_to_close,
    MAX(CASE WHEN row_num = CAST(ROUND(0.90 * total_closed) AS INTEGER) THEN days_to_close END) AS p90_days_to_close,
    MAX(days_to_close) AS max_days
FROM ordered_leads_origin
GROUP BY lead_origin, total_closed
ORDER BY median_days_to_close ASC;

-- Time-to-close distribution by Business Segment
WITH ordered_leads_segment AS (
    SELECT 
        s.segment_name AS business_segment,
        f.days_to_close,
        ROW_NUMBER() OVER (PARTITION BY s.segment_name ORDER BY f.days_to_close) AS row_num,
        COUNT(*) OVER (PARTITION BY s.segment_name) AS total_closed
    FROM fact_lead f
    JOIN dim_segment s ON f.segment_key = s.segment_key
    WHERE f.is_won = 1 AND f.days_to_close IS NOT NULL
)
SELECT 
    business_segment,
    total_closed,
    MIN(days_to_close) AS min_days,
    MAX(CASE WHEN row_num = CAST(ROUND(0.50 * total_closed) AS INTEGER) THEN days_to_close END) AS median_days_to_close,
    MAX(CASE WHEN row_num = CAST(ROUND(0.75 * total_closed) AS INTEGER) THEN days_to_close END) AS p75_days_to_close,
    MAX(CASE WHEN row_num = CAST(ROUND(0.90 * total_closed) AS INTEGER) THEN days_to_close END) AS p90_days_to_close
FROM ordered_leads_segment
GROUP BY business_segment, total_closed
ORDER BY median_days_to_close ASC;
