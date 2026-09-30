-- 04_seller_revenue_by_origin.sql: Post-Signing Revenue & Seller Performance by Lead Origin
-- Answers: Which acquisition channels generate the highest revenue and best customer satisfaction AFTER seller onboarding?
-- Condition: Restricts to order items placed on or after the seller's won_date (days_after_won >= 0).
-- Metrics: Revenue, Orders, Active Sellers, Revenue per Closed Deal, Revenue per Active Seller, AOV, Review Score, Freight Share.

WITH seller_orders_post_won AS (
    SELECT 
        sel.seller_id,
        o.origin_name AS lead_origin,
        COUNT(DISTINCT foi.order_id) AS total_orders,
        COUNT(foi.order_item_key) AS total_items,
        SUM(foi.price) AS total_product_revenue,
        SUM(foi.freight_value) AS total_freight_revenue,
        SUM(foi.price + foi.freight_value) AS total_gmv,
        AVG(foi.review_score) AS avg_review_score
    FROM fact_order_item foi
    JOIN dim_seller sel ON foi.seller_key = sel.seller_key
    JOIN fact_lead fl ON sel.seller_id = fl.mql_id OR sel.seller_key = fl.seller_key
    JOIN dim_origin o ON fl.origin_key = o.origin_key
    WHERE foi.days_after_won >= 0 AND foi.order_status != 'canceled'
    GROUP BY sel.seller_id, o.origin_name
),
closed_deals_count AS (
    SELECT 
        o.origin_name AS lead_origin,
        COUNT(DISTINCT fl.seller_key) AS total_closed_deals,
        COUNT(fl.lead_key) AS total_mqls
    FROM fact_lead fl
    JOIN dim_origin o ON fl.origin_key = o.origin_key
    WHERE fl.is_won = 1
    GROUP BY o.origin_name
)
SELECT 
    cdc.lead_origin,
    cdc.total_mqls,
    cdc.total_closed_deals,
    COUNT(DISTINCT sop.seller_id) AS active_sellers,
    ROUND(CAST(COUNT(DISTINCT sop.seller_id) AS FLOAT) / cdc.total_closed_deals, 4) AS seller_activation_rate,
    COALESCE(SUM(sop.total_orders), 0) AS total_post_signing_orders,
    COALESCE(ROUND(SUM(sop.total_product_revenue), 2), 0.0) AS total_post_signing_revenue,
    COALESCE(ROUND(SUM(sop.total_product_revenue) / cdc.total_closed_deals, 2), 0.0) AS revenue_per_closed_deal,
    COALESCE(ROUND(SUM(sop.total_product_revenue) / NULLIF(COUNT(DISTINCT sop.seller_id), 0), 2), 0.0) AS revenue_per_active_seller,
    COALESCE(ROUND(SUM(sop.total_product_revenue) / NULLIF(SUM(sop.total_orders), 0), 2), 0.0) AS average_order_value_aov,
    COALESCE(ROUND(SUM(sop.total_freight_revenue) / NULLIF(SUM(sop.total_gmv), 0), 4), 0.0) AS freight_revenue_share,
    COALESCE(ROUND(AVG(sop.avg_review_score), 2), 0.0) AS avg_review_score,
    DENSE_RANK() OVER (ORDER BY COALESCE(SUM(sop.total_product_revenue) / cdc.total_closed_deals, 0) DESC) AS revenue_per_deal_rank
FROM closed_deals_count cdc
LEFT JOIN seller_orders_post_won sop ON cdc.lead_origin = sop.lead_origin
GROUP BY cdc.lead_origin, cdc.total_mqls, cdc.total_closed_deals
ORDER BY total_post_signing_revenue DESC;
