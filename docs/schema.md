# Olist Marketing Funnel & E-Commerce Star Schema Architecture

> **Data Warehouse Schema**: `dw`  
> **Grain Architecture**: Dual Fact Tables linked via Conformed Dimensions  

---

## 1. Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    dim_date ||--o{ fact_lead : "date_key_first_contact"
    dim_date ||--o{ fact_lead : "date_key_won"
    dim_date ||--o{ fact_order_item : "date_key_purchase"
    dim_origin ||--o{ fact_lead : "origin_key"
    dim_landing_page ||--o{ fact_lead : "landing_page_key"
    dim_segment ||--o{ fact_lead : "segment_key"
    dim_sdr ||--o{ fact_lead : "sdr_key"
    dim_sr ||--o{ fact_lead : "sr_key"
    dim_seller ||--o{ fact_lead : "seller_key"
    dim_seller ||--o{ fact_order_item : "seller_key"
    dim_product ||--o{ fact_order_item : "product_key"
    dim_customer ||--o{ fact_order_item : "customer_key"

    fact_lead {
        int lead_key PK
        string mql_id UK
        int date_key_first_contact FK
        int origin_key FK
        int landing_page_key FK
        int is_won
        int date_key_won FK
        int days_to_close
        int seller_key FK
        int segment_key FK
        int sdr_key FK
        int sr_key FK
    }

    fact_order_item {
        int order_item_key PK
        string order_id
        int order_item_id
        int date_key_purchase FK
        int seller_key FK
        int product_key FK
        int customer_key FK
        decimal price
        decimal freight_value
        string order_status
        int review_score
        int days_after_won
    }

    dim_seller {
        int seller_key PK
        string seller_id UK
        timestamp won_date
        string lead_type
        string lead_behaviour_profile
        string business_type
        decimal declared_monthly_revenue
        int declared_product_catalog_size
        string average_stock
        int has_company
        int has_gtin
        string city
        string state
    }

    dim_origin {
        int origin_key PK
        string origin_name UK
    }

    dim_date {
        int date_key PK
        date full_date
        int year
        int quarter
        int month
        string month_name
        int day_of_month
        int day_of_week
        int week_of_year
    }

    dim_segment {
        int segment_key PK
        string segment_name UK
    }

    dim_landing_page {
        int landing_page_key PK
        string landing_page_id UK
    }

    dim_sdr {
        int sdr_key PK
        string sdr_id UK
    }

    dim_sr {
        int sr_key PK
        string sr_id UK
    }

    dim_product {
        int product_key PK
        string product_id UK
        string category_name_pt
        string category_name_en
        int weight_g
    }

    dim_customer {
        int customer_key PK
        string customer_id UK
        string customer_unique_id
        string city
        string state
    }
```

---

## 2. Table Grain & Business Logic Summary

### Fact Tables
1. **`fact_lead`**: 
   - **Grain**: One row per Marketing Qualified Lead (`mql_id`).
   - **Surrogate Key**: `lead_key`.
   - **Metrics**: `is_won` (0/1), `days_to_close` (won_date minus first_contact_date).
   - **Null Handling**: Missing origin explicitly converted to `'unknown'`. Unwon leads have `date_key_won = NULL` and `days_to_close = NULL`.

2. **`fact_order_item`**:
   - **Grain**: One row per individual order line item (`order_id`, `order_item_id`).
   - **Surrogate Key**: `order_item_key`.
   - **Metrics**: `price`, `freight_value`, `review_score`, `days_after_won` (order purchase timestamp minus seller won_date).
   - **Filter Logic**: Restricts post-signing performance calculations to `days_after_won >= 0`.

### Dimension Tables
- **`dim_date`**: Conformed date dimension spanning 2017 to 2019. Key format: `YYYYMMDD`.
- **`dim_origin`**: Marketing acquisition channels (`paid_search`, `organic_search`, `referral`, `email`, `social`, `direct_traffic`, `organic_social`, `display`, `other`, `unknown`).
- **`dim_seller`**: Conformed dimension containing firmographic and onboarding profiles (`lead_type`, `lead_behaviour_profile`, `declared_monthly_revenue`, catalog size).
- **`dim_segment`, `dim_sdr`, `dim_sr`, `dim_product`, `dim_customer`**: Conformed lookup dimensions.
