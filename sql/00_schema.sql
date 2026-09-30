-- Star Schema DDL for Marketing Funnel & Revenue Analytics
-- Supports both PostgreSQL and SQLite dialect syntax

-- Drop existing tables if re-initialising
DROP TABLE IF EXISTS fact_order_item;
DROP TABLE IF EXISTS fact_lead;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_origin;
DROP TABLE IF EXISTS dim_landing_page;
DROP TABLE IF EXISTS dim_seller;
DROP TABLE IF EXISTS dim_segment;
DROP TABLE IF EXISTS dim_sdr;
DROP TABLE IF EXISTS dim_sr;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_customer;

-- Dimension 1: Date Dimension
CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name VARCHAR(15) NOT NULL,
    day_of_month INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    week_of_year INTEGER NOT NULL
);

-- Dimension 2: Lead Origin (NULL origin mapped to 'unknown')
CREATE TABLE dim_origin (
    origin_key INTEGER PRIMARY KEY,
    origin_name VARCHAR(50) NOT NULL UNIQUE
);

-- Dimension 3: Landing Page
CREATE TABLE dim_landing_page (
    landing_page_key INTEGER PRIMARY KEY,
    landing_page_id VARCHAR(64) NOT NULL UNIQUE
);

-- Dimension 4: Seller Dimension (contains firmographic & closed deal attributes)
CREATE TABLE dim_seller (
    seller_key INTEGER PRIMARY KEY,
    seller_id VARCHAR(64) NOT NULL UNIQUE,
    won_date TIMESTAMP,
    lead_type VARCHAR(50),
    lead_behaviour_profile VARCHAR(50),
    business_type VARCHAR(50),
    declared_monthly_revenue DECIMAL(12,2),
    declared_product_catalog_size INTEGER,
    average_stock VARCHAR(20),
    has_company INTEGER DEFAULT 0,
    has_gtin INTEGER DEFAULT 0,
    city VARCHAR(100),
    state VARCHAR(10)
);

-- Dimension 5: Business Segment
CREATE TABLE dim_segment (
    segment_key INTEGER PRIMARY KEY,
    segment_name VARCHAR(100) NOT NULL UNIQUE
);

-- Dimension 6: Sales Development Representative (SDR)
CREATE TABLE dim_sdr (
    sdr_key INTEGER PRIMARY KEY,
    sdr_id VARCHAR(64) NOT NULL UNIQUE
);

-- Dimension 7: Sales Representative (SR)
CREATE TABLE dim_sr (
    sr_key INTEGER PRIMARY KEY,
    sr_id VARCHAR(64) NOT NULL UNIQUE
);

-- Dimension 8: Product Dimension
CREATE TABLE dim_product (
    product_key INTEGER PRIMARY KEY,
    product_id VARCHAR(64) NOT NULL UNIQUE,
    category_name_pt VARCHAR(100),
    category_name_en VARCHAR(100),
    weight_g INTEGER
);

-- Dimension 9: Customer Dimension
CREATE TABLE dim_customer (
    customer_key INTEGER PRIMARY KEY,
    customer_id VARCHAR(64) NOT NULL UNIQUE,
    customer_unique_id VARCHAR(64),
    city VARCHAR(100),
    state VARCHAR(10)
);

-- Fact Table 1: Marketing Qualified Leads (Fact Lead)
-- Grain: One row per MQL
CREATE TABLE fact_lead (
    lead_key INTEGER PRIMARY KEY,
    mql_id VARCHAR(64) NOT NULL UNIQUE,
    date_key_first_contact INTEGER NOT NULL REFERENCES dim_date(date_key),
    origin_key INTEGER NOT NULL REFERENCES dim_origin(origin_key),
    landing_page_key INTEGER NOT NULL REFERENCES dim_landing_page(landing_page_key),
    is_won INTEGER NOT NULL CHECK (is_won IN (0, 1)),
    date_key_won INTEGER REFERENCES dim_date(date_key),
    days_to_close INTEGER,
    seller_key INTEGER REFERENCES dim_seller(seller_key),
    segment_key INTEGER NOT NULL REFERENCES dim_segment(segment_key),
    sdr_key INTEGER NOT NULL REFERENCES dim_sdr(sdr_key),
    sr_key INTEGER NOT NULL REFERENCES dim_sr(sr_key)
);

-- Fact Table 2: E-Commerce Post-Signing Order Items (Fact Order Item)
-- Grain: One row per order item
CREATE TABLE fact_order_item (
    order_item_key INTEGER PRIMARY KEY,
    order_id VARCHAR(64) NOT NULL,
    order_item_id INTEGER NOT NULL,
    date_key_purchase INTEGER NOT NULL REFERENCES dim_date(date_key),
    seller_key INTEGER NOT NULL REFERENCES dim_seller(seller_key),
    product_key INTEGER NOT NULL REFERENCES dim_product(product_key),
    customer_key INTEGER NOT NULL REFERENCES dim_customer(customer_key),
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0),
    freight_value DECIMAL(10,2) NOT NULL CHECK (freight_value >= 0),
    order_status VARCHAR(30) NOT NULL,
    review_score INTEGER CHECK (review_score BETWEEN 1 AND 5),
    days_after_won INTEGER,
    CONSTRAINT idx_order_item_unique UNIQUE (order_id, order_item_id)
);

-- Indexes for performance & quick foreign key lookups
CREATE INDEX idx_fact_lead_origin ON fact_lead(origin_key);
CREATE INDEX idx_fact_lead_won ON fact_lead(is_won);
CREATE INDEX idx_fact_lead_date_fc ON fact_lead(date_key_first_contact);
CREATE INDEX idx_fact_order_item_seller ON fact_order_item(seller_key);
CREATE INDEX idx_fact_order_item_date ON fact_order_item(date_key_purchase);
