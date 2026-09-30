"""
ETL Pipeline: Reads raw Olist CSVs, executes Star Schema DDL, populates DW facts and dimensions,
handles missing data (e.g. origin NULL -> 'unknown'), computes metrics, and exports processed datasets.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from sqlalchemy import text
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.db import get_engine

def load_data_pipeline(raw_dir="data/raw", processed_dir="data/processed"):
    """
    Executes complete ETL workflow.
    """
    os.makedirs(processed_dir, exist_ok=True)
    engine = get_engine()

    print("[ETL] Starting Marketing Funnel Data Pipeline...")

    # 1. Read Raw Datasets
    print("  -> Loading raw CSV files from data/raw/...")
    df_mql = pd.read_csv(os.path.join(raw_dir, 'olist_marketing_qualified_leads_dataset.csv'))
    df_closed = pd.read_csv(os.path.join(raw_dir, 'olist_closed_deals_dataset.csv'))
    df_orders = pd.read_csv(os.path.join(raw_dir, 'olist_orders_dataset.csv'))
    df_items = pd.read_csv(os.path.join(raw_dir, 'olist_order_items_dataset.csv'))
    df_payments = pd.read_csv(os.path.join(raw_dir, 'olist_order_payments_dataset.csv'))
    df_reviews = pd.read_csv(os.path.join(raw_dir, 'olist_order_reviews_dataset.csv'))
    df_customers = pd.read_csv(os.path.join(raw_dir, 'olist_customers_dataset.csv'))
    df_sellers = pd.read_csv(os.path.join(raw_dir, 'olist_sellers_dataset.csv'))
    df_products = pd.read_csv(os.path.join(raw_dir, 'olist_products_dataset.csv'))
    df_trans = pd.read_csv(os.path.join(raw_dir, 'product_category_name_translation.csv'))

    # 2. Execute Schema DDL
    print("  -> Initialising Star Schema DDL...")
    with open('sql/00_schema.sql', 'r', encoding='utf-8') as f:
        ddl_sql = f.read()

    with engine.connect() as conn:
        for statement in ddl_sql.split(';'):
            stmt = statement.strip()
            if stmt:
                conn.execute(text(stmt))
        conn.commit()

    # 3. Clean & Transform Dimensions

    # Origin Dimension (Handle NULL origin -> 'unknown')
    df_mql['origin_clean'] = df_mql['origin'].fillna('unknown').str.strip().str.lower()
    origins_unique = sorted(df_mql['origin_clean'].unique())
    df_dim_origin = pd.DataFrame({
        'origin_key': range(1, len(origins_unique) + 1),
        'origin_name': origins_unique
    })
    origin_map = dict(zip(df_dim_origin['origin_name'], df_dim_origin['origin_key']))

    # Landing Page Dimension
    landing_pages = sorted(df_mql['landing_page_id'].dropna().unique())
    df_dim_landing = pd.DataFrame({
        'landing_page_key': range(1, len(landing_pages) + 1),
        'landing_page_id': landing_pages
    })
    landing_map = dict(zip(df_dim_landing['landing_page_id'], df_dim_landing['landing_page_key']))

    # SDR & SR Dimensions
    sdrs = sorted(df_closed['sdr_id'].dropna().unique())
    df_dim_sdr = pd.DataFrame({
        'sdr_key': range(1, len(sdrs) + 1),
        'sdr_id': sdrs
    })
    sdr_map = dict(zip(df_dim_sdr['sdr_id'], df_dim_sdr['sdr_key']))

    srs = sorted(df_closed['sr_id'].dropna().unique())
    df_dim_sr = pd.DataFrame({
        'sr_key': range(1, len(srs) + 1),
        'sr_id': srs
    })
    sr_map = dict(zip(df_dim_sr['sr_id'], df_dim_sr['sr_key']))

    # Segment Dimension
    df_closed['business_segment_clean'] = df_closed['business_segment'].fillna('unknown').str.strip().str.lower()
    segments = sorted(df_closed['business_segment_clean'].unique())
    if 'unknown' not in segments:
        segments.append('unknown')
    df_dim_segment = pd.DataFrame({
        'segment_key': range(1, len(segments) + 1),
        'segment_name': segments
    })
    segment_map = dict(zip(df_dim_segment['segment_name'], df_dim_segment['segment_key']))

    # Customer Dimension
    df_dim_customer = pd.DataFrame({
        'customer_key': range(1, len(df_customers) + 1),
        'customer_id': df_customers['customer_id'],
        'customer_unique_id': df_customers['customer_unique_id'],
        'city': df_customers['customer_city'],
        'state': df_customers['customer_state']
    })
    customer_map = dict(zip(df_dim_customer['customer_id'], df_dim_customer['customer_key']))

    # Product Dimension
    df_prod_merged = df_products.merge(df_trans, on='product_category_name', how='left')
    df_dim_product = pd.DataFrame({
        'product_key': range(1, len(df_prod_merged) + 1),
        'product_id': df_prod_merged['product_id'],
        'category_name_pt': df_prod_merged['product_category_name'].fillna('outros'),
        'category_name_en': df_prod_merged['product_category_name_english'].fillna('other'),
        'weight_g': df_prod_merged['product_weight_g'].fillna(0).astype(int)
    })
    product_map = dict(zip(df_dim_product['product_id'], df_dim_product['product_key']))

    # Seller Dimension (Combine sellers info + closed deal specs)
    df_sellers_full = df_sellers.merge(df_closed, on='seller_id', how='left')
    df_dim_seller = pd.DataFrame({
        'seller_key': range(1, len(df_sellers_full) + 1),
        'seller_id': df_sellers_full['seller_id'],
        'won_date': df_sellers_full['won_date'],
        'lead_type': df_sellers_full['lead_type'].fillna('unknown'),
        'lead_behaviour_profile': df_sellers_full['lead_behaviour_profile'].fillna('unknown'),
        'business_type': df_sellers_full['business_type'].fillna('unknown'),
        'declared_monthly_revenue': df_sellers_full['declared_monthly_revenue'].fillna(0.0),
        'declared_product_catalog_size': df_sellers_full['declared_product_catalog_size'].fillna(0).astype(int),
        'average_stock': df_sellers_full['average_stock'].fillna('unknown'),
        'has_company': df_sellers_full['has_company'].fillna(0).astype(int),
        'has_gtin': df_sellers_full['has_gtin'].fillna(0).astype(int),
        'city': df_sellers_full['seller_city'],
        'state': df_sellers_full['seller_state']
    })
    seller_map = dict(zip(df_dim_seller['seller_id'], df_dim_seller['seller_key']))
    seller_won_map = dict(zip(df_dim_seller['seller_id'], pd.to_datetime(df_dim_seller['won_date'])))

    # Date Dimension Construction (2017 to 2019)
    all_dates = pd.date_range(start='2017-01-01', end='2019-12-31', freq='D')
    df_dim_date = pd.DataFrame({
        'date_key': all_dates.strftime('%Y%m%d').astype(int),
        'full_date': all_dates.date,
        'year': all_dates.year,
        'quarter': all_dates.quarter,
        'month': all_dates.month,
        'month_name': all_dates.strftime('%B'),
        'day_of_month': all_dates.day,
        'day_of_week': all_dates.dayofweek + 1,
        'week_of_year': all_dates.isocalendar().week
    })
    
    print("  -> Loading dimension tables into Data Warehouse...")
    df_dim_date.to_sql('dim_date', engine, if_exists='append', index=False)
    df_dim_origin.to_sql('dim_origin', engine, if_exists='append', index=False)
    df_dim_landing.to_sql('dim_landing_page', engine, if_exists='append', index=False)
    df_dim_sdr.to_sql('dim_sdr', engine, if_exists='append', index=False)
    df_dim_sr.to_sql('dim_sr', engine, if_exists='append', index=False)
    df_dim_segment.to_sql('dim_segment', engine, if_exists='append', index=False)
    df_dim_customer.to_sql('dim_customer', engine, if_exists='append', index=False)
    df_dim_product.to_sql('dim_product', engine, if_exists='append', index=False)
    df_dim_seller.to_sql('dim_seller', engine, if_exists='append', index=False)

    # 4. Build Fact Lead (Grain: 1 row per MQL)
    print("  -> Building Fact Lead table...")
    mql_merged = df_mql.merge(df_closed, on='mql_id', how='left')
    
    mql_merged['first_contact_dt'] = pd.to_datetime(mql_merged['first_contact_date'])
    mql_merged['won_dt'] = pd.to_datetime(mql_merged['won_date'])

    # Date keys
    mql_merged['date_key_first_contact'] = mql_merged['first_contact_dt'].dt.strftime('%Y%m%d').astype(int)
    mql_merged['date_key_won'] = mql_merged['won_dt'].dt.strftime('%Y%m%d')
    mql_merged['date_key_won'] = mql_merged['date_key_won'].apply(lambda x: int(x) if pd.notna(x) else None)

    # Days to close
    mql_merged['is_won'] = mql_merged['seller_id'].notna().astype(int)
    mql_merged['days_to_close'] = (mql_merged['won_dt'] - mql_merged['first_contact_dt']).dt.days

    # Key Mappings
    mql_merged['origin_key'] = mql_merged['origin_clean'].map(origin_map)
    mql_merged['landing_page_key'] = mql_merged['landing_page_id'].map(landing_map).fillna(1).astype(int)
    mql_merged['seller_key'] = mql_merged['seller_id'].map(seller_map)
    mql_merged['segment_key'] = mql_merged['business_segment_clean'].map(segment_map).fillna(segment_map.get('unknown', 1)).astype(int)
    mql_merged['sdr_key'] = mql_merged['sdr_id'].map(sdr_map).fillna(1).astype(int)
    mql_merged['sr_key'] = mql_merged['sr_id'].map(sr_map).fillna(1).astype(int)

    df_fact_lead = pd.DataFrame({
        'lead_key': range(1, len(mql_merged) + 1),
        'mql_id': mql_merged['mql_id'],
        'date_key_first_contact': mql_merged['date_key_first_contact'],
        'origin_key': mql_merged['origin_key'],
        'landing_page_key': mql_merged['landing_page_key'],
        'is_won': mql_merged['is_won'],
        'date_key_won': mql_merged['date_key_won'],
        'days_to_close': mql_merged['days_to_close'],
        'seller_key': mql_merged['seller_key'],
        'segment_key': mql_merged['segment_key'],
        'sdr_key': mql_merged['sdr_key'],
        'sr_key': mql_merged['sr_key']
    })

    df_fact_lead.to_sql('fact_lead', engine, if_exists='append', index=False)
    print(f"  [OK] Fact Lead populated: {len(df_fact_lead)} rows")

    # 5. Build Fact Order Item (Grain: 1 row per order item)
    print("  -> Building Fact Order Item table...")
    items_merged = df_items.merge(df_orders, on='order_id', how='inner')
    
    # Merge avg review score per order
    reviews_avg = df_reviews.groupby('order_id')['review_score'].mean().reset_index()
    items_merged = items_merged.merge(reviews_avg, on='order_id', how='left')

    items_merged['purchase_dt'] = pd.to_datetime(items_merged['order_purchase_timestamp'])
    items_merged['date_key_purchase'] = items_merged['purchase_dt'].dt.strftime('%Y%m%d').astype(int)

    items_merged['seller_key'] = items_merged['seller_id'].map(seller_map)
    items_merged['product_key'] = items_merged['product_id'].map(product_map)
    items_merged['customer_key'] = items_merged['customer_id'].map(customer_map)

    # Filter out order items without mapped sellers/products/customers
    items_valid = items_merged.dropna(subset=['seller_key', 'product_key', 'customer_key']).copy()
    items_valid['seller_key'] = items_valid['seller_key'].astype(int)
    items_valid['product_key'] = items_valid['product_key'].astype(int)
    items_valid['customer_key'] = items_valid['customer_key'].astype(int)

    # Days after won calculation
    items_valid['won_date'] = items_valid['seller_id'].map(seller_won_map)
    items_valid['days_after_won'] = (items_valid['purchase_dt'] - items_valid['won_date']).dt.days

    df_fact_order_item = pd.DataFrame({
        'order_item_key': range(1, len(items_valid) + 1),
        'order_id': items_valid['order_id'],
        'order_item_id': items_valid['order_item_id'],
        'date_key_purchase': items_valid['date_key_purchase'],
        'seller_key': items_valid['seller_key'],
        'product_key': items_valid['product_key'],
        'customer_key': items_valid['customer_key'],
        'price': items_valid['price'],
        'freight_value': items_valid['freight_value'],
        'order_status': items_valid['order_status'],
        'review_score': items_valid['review_score'].round().astype('Int64'),
        'days_after_won': items_valid['days_after_won']
    })

    df_fact_order_item.to_sql('fact_order_item', engine, if_exists='append', index=False)
    print(f"  [OK] Fact Order Item populated: {len(df_fact_order_item)} rows")

    # 6. Export Processed Dataframes to data/processed/
    print("  -> Exporting processed CSV tables for Power BI and Analytics...")
    df_dim_date.to_csv(os.path.join(processed_dir, 'dim_date.csv'), index=False)
    df_dim_origin.to_csv(os.path.join(processed_dir, 'dim_origin.csv'), index=False)
    df_dim_landing.to_csv(os.path.join(processed_dir, 'dim_landing_page.csv'), index=False)
    df_dim_seller.to_csv(os.path.join(processed_dir, 'dim_seller.csv'), index=False)
    df_dim_segment.to_csv(os.path.join(processed_dir, 'dim_segment.csv'), index=False)
    df_dim_product.to_csv(os.path.join(processed_dir, 'dim_product.csv'), index=False)
    df_dim_customer.to_csv(os.path.join(processed_dir, 'dim_customer.csv'), index=False)
    df_fact_lead.to_csv(os.path.join(processed_dir, 'fact_lead.csv'), index=False)
    df_fact_order_item.to_csv(os.path.join(processed_dir, 'fact_order_item.csv'), index=False)

    print("[ETL] Data Pipeline completed successfully!")

if __name__ == '__main__':
    load_data_pipeline()
