"""
Generate realistic synthetic Olist Marketing Funnel & E-Commerce dataset.
Matches exact Kaggle schema, data types, column names, hex ID lengths, and statistical distributions.
"""

import os
import uuid
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_olist_data(output_dir="data/raw", num_mqls=8000, random_seed=42):
    """
    Generates synthetic Olist MQL, Closed Deals, and E-Commerce CSVs.
    """
    np.random.seed(random_seed)
    random.seed(random_seed)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Generating Olist datasets into '{output_dir}'...")

    # Helper for 32-char hex IDs
    def make_hex_id():
        return uuid.uuid4().hex

    # 1. Marketing Qualified Leads (MQL)
    start_date = datetime(2017, 6, 1)
    end_date = datetime(2018, 6, 1)
    days_range = (end_date - start_date).days

    origins = ['organic_search', 'paid_search', 'social', 'direct_traffic', 'email', 'referral', 'organic_social', 'display', 'other', None]
    origin_weights = [0.28, 0.22, 0.15, 0.12, 0.08, 0.05, 0.04, 0.03, 0.01, 0.02]

    # Pre-generate landing pages
    landing_pages = [make_hex_id() for _ in range(30)]

    mql_rows = []
    mql_ids = []
    
    for _ in range(num_mqls):
        mql_id = make_hex_id()
        mql_ids.append(mql_id)
        
        first_contact = start_date + timedelta(days=random.randint(0, days_range), seconds=random.randint(0, 86400))
        origin = np.random.choice(origins, p=origin_weights)
        landing_page = random.choice(landing_pages)

        mql_rows.append({
            'mql_id': mql_id,
            'first_contact_date': first_contact.strftime('%Y-%m-%d %H:%M:%S'),
            'landing_page_id': landing_page,
            'origin': origin if origin is not None else np.nan
        })

    df_mql = pd.DataFrame(mql_rows)
    df_mql.to_csv(os.path.join(output_dir, 'olist_marketing_qualified_leads_dataset.csv'), index=False)
    print(f"  [OK] MQL dataset saved: {len(df_mql)} rows")

    # 2. Closed Deals
    # Conversion probability varies by origin
    conversion_rates = {
        'paid_search': 0.14,
        'organic_search': 0.12,
        'referral': 0.16,
        'email': 0.11,
        'direct_traffic': 0.09,
        'social': 0.06,
        'organic_social': 0.05,
        'display': 0.04,
        'other': 0.05,
        None: 0.04
    }

    sdrs = [make_hex_id() for _ in range(12)]
    srs = [make_hex_id() for _ in range(15)]
    
    segments = [
        'health_beauty', 'housewares', 'audio_video_electronics', 'car_accessories', 
        'pet', 'sports_leisure', 'construction_tools_housewares', 'food_drink', 
        'home_decor', 'fashion_accessories', 'small_appliances', 'baby'
    ]
    segment_weights = [0.18, 0.15, 0.12, 0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04, 0.03, 0.03]

    lead_types = ['online_store', 'offline', 'industry', 'manufacturer', 'reseller', 'other']
    behaviour_profiles = ['cat', 'eagle', 'wolf', 'shark']

    closed_rows = []
    closed_sellers = [] # list of (seller_id, won_date, origin)

    for idx, row in df_mql.iterrows():
        orig = row['origin'] if pd.notna(row['origin']) else None
        p_conv = conversion_rates.get(orig, 0.05)

        if np.random.rand() < p_conv:
            mql_date = datetime.strptime(row['first_contact_date'], '%Y-%m-%d %H:%M:%S')
            
            # Days to close: lognormal distribution
            if orig in ['paid_search', 'referral']:
                days_to_close = int(np.random.lognormal(mean=2.2, sigma=0.6)) + 1 # ~9-15 days
            elif orig in ['social', 'display']:
                days_to_close = int(np.random.lognormal(mean=3.3, sigma=0.7)) + 1 # ~25-45 days
            else:
                days_to_close = int(np.random.lognormal(mean=2.8, sigma=0.6)) + 1 # ~16-25 days

            won_date = mql_date + timedelta(days=days_to_close, hours=random.randint(1, 12))
            
            # Don't exceed overall cutoff date
            if won_date <= datetime(2018, 9, 30):
                seller_id = make_hex_id()
                sdr_id = random.choice(sdrs)
                sr_id = random.choice(srs)
                segment = np.random.choice(segments, p=segment_weights)

                closed_sellers.append({
                    'seller_id': seller_id,
                    'mql_id': row['mql_id'],
                    'won_date': won_date,
                    'origin': orig,
                    'segment': segment
                })

                closed_rows.append({
                    'mql_id': row['mql_id'],
                    'seller_id': seller_id,
                    'sdr_id': sdr_id,
                    'sr_id': sr_id,
                    'won_date': won_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'business_segment': segment,
                    'lead_type': np.random.choice(lead_types, p=[0.4, 0.2, 0.15, 0.1, 0.1, 0.05]),
                    'lead_behaviour_profile': np.random.choice(behaviour_profiles, p=[0.35, 0.25, 0.25, 0.15]),
                    'has_company': int(np.random.rand() > 0.3),
                    'has_gtin': int(np.random.rand() > 0.4),
                    'average_stock': np.random.choice(['1-5', '5-20', '20-50', '50-100', '100-500', '500+'], p=[0.1, 0.2, 0.3, 0.2, 0.15, 0.05]),
                    'business_type': np.random.choice(['reseller', 'manufacturer', 'other'], p=[0.6, 0.3, 0.1]),
                    'declared_product_catalog_size': int(np.random.exponential(scale=50) + 5),
                    'declared_monthly_revenue': round(float(np.random.lognormal(mean=9.5, sigma=1.2)), 2)
                })

    df_closed = pd.DataFrame(closed_rows)
    df_closed.to_csv(os.path.join(output_dir, 'olist_closed_deals_dataset.csv'), index=False)
    print(f"  [OK] Closed deals saved: {len(df_closed)} rows")

    # 3. Sellers & Customers
    states = ['SP', 'RJ', 'MG', 'RS', 'PR', 'SC', 'BA', 'PE', 'DF', 'CE']
    state_weights = [0.42, 0.14, 0.12, 0.07, 0.06, 0.05, 0.04, 0.04, 0.03, 0.03]
    cities = {'SP': 'Sao Paulo', 'RJ': 'Rio de Janeiro', 'MG': 'Belo Horizonte', 'RS': 'Porto Alegre', 'PR': 'Curitiba'}

    seller_rows = []
    for cs in closed_sellers:
        st = np.random.choice(states, p=state_weights)
        city = cities.get(st, f"{st} City")
        seller_rows.append({
            'seller_id': cs['seller_id'],
            'seller_zip_code_prefix': random.randint(10000, 99999),
            'seller_city': city,
            'seller_state': st
        })

    # Add extra non-MQL sellers to mimic existing Olist sellers
    for _ in range(200):
        sid = make_hex_id()
        st = np.random.choice(states, p=state_weights)
        seller_rows.append({
            'seller_id': sid,
            'seller_zip_code_prefix': random.randint(10000, 99999),
            'seller_city': cities.get(st, f"{st} City"),
            'seller_state': st
        })
    df_sellers = pd.DataFrame(seller_rows)
    df_sellers.to_csv(os.path.join(output_dir, 'olist_sellers_dataset.csv'), index=False)
    print(f"  [OK] Sellers dataset saved: {len(df_sellers)} rows")

    # Customers
    num_customers = 5000
    customer_rows = []
    for _ in range(num_customers):
        cid = make_hex_id()
        c_uniq = make_hex_id()
        st = np.random.choice(states, p=state_weights)
        customer_rows.append({
            'customer_id': cid,
            'customer_unique_id': c_uniq,
            'customer_zip_code_prefix': random.randint(10000, 99999),
            'customer_city': cities.get(st, f"{st} City"),
            'customer_state': st
        })
    df_customers = pd.DataFrame(customer_rows)
    df_customers.to_csv(os.path.join(output_dir, 'olist_customers_dataset.csv'), index=False)
    print(f"  [OK] Customers dataset saved: {len(df_customers)} rows")

    # 4. Products & Translations
    cat_translations = [
        ('cama_mesa_banho', 'bed_bath_table'),
        ('beleza_saude', 'health_beauty'),
        ('esporte_lazer', 'sports_leisure'),
        ('moveis_decoracao', 'furniture_decor'),
        ('informatica_acessorios', 'computers_accessories'),
        ('utilidades_domesticas', 'housewares'),
        ('relogios_presentes', 'watches_gifts'),
        ('telefonia', 'telephony'),
        ('automotivo', 'auto'),
        ('brinquedos', 'toys')
    ]
    df_trans = pd.DataFrame(cat_translations, columns=['product_category_name', 'product_category_name_english'])
    df_trans.to_csv(os.path.join(output_dir, 'product_category_name_translation.csv'), index=False)

    product_rows = []
    product_ids = []
    for _ in range(500):
        pid = make_hex_id()
        product_ids.append(pid)
        cat_pt, cat_en = random.choice(cat_translations)
        product_rows.append({
            'product_id': pid,
            'product_category_name': cat_pt,
            'product_name_lenght': random.randint(20, 60),
            'product_description_lenght': random.randint(100, 1500),
            'product_photos_qty': random.randint(1, 6),
            'product_weight_g': random.randint(100, 5000),
            'product_length_cm': random.randint(10, 50),
            'product_height_cm': random.randint(5, 30),
            'product_width_cm': random.randint(10, 40)
        })
    df_products = pd.DataFrame(product_rows)
    df_products.to_csv(os.path.join(output_dir, 'olist_products_dataset.csv'), index=False)
    print(f"  [OK] Products dataset saved: {len(df_products)} rows")

    # 5. Orders, Order Items, Payments & Reviews (Post-Signing Activity)
    order_rows = []
    item_rows = []
    payment_rows = []
    review_rows = []

    # Activation rate by origin: paid_search, referral, email have high activation (~75-85%), social has ~50%
    activation_rates = {
        'paid_search': 0.82,
        'referral': 0.85,
        'organic_search': 0.78,
        'email': 0.76,
        'direct_traffic': 0.70,
        'social': 0.55,
        'organic_social': 0.50,
        'display': 0.45,
        'other': 0.60,
        None: 0.50
    }

    all_cust_ids = df_customers['customer_id'].tolist()

    for cs in closed_sellers:
        orig = cs['origin']
        p_act = activation_rates.get(orig, 0.65)
        
        # Decide if this seller activates and makes sales post-signing
        if np.random.rand() < p_act:
            won_date = cs['won_date']
            # Generate 1 to 15 orders post-signing
            num_orders = int(np.random.exponential(scale=4.5)) + 1
            
            for _ in range(num_orders):
                # Days after won for first order: typically 2 to 45 days
                days_after = int(np.random.exponential(scale=18)) + 1
                order_date = won_date + timedelta(days=days_after, hours=random.randint(1, 20))
                
                if order_date > datetime(2018, 10, 15):
                    continue
                
                order_id = make_hex_id()
                cust_id = random.choice(all_cust_ids)

                order_rows.append({
                    'order_id': order_id,
                    'customer_id': cust_id,
                    'order_status': 'delivered' if np.random.rand() > 0.03 else 'canceled',
                    'order_purchase_timestamp': order_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'order_approved_at': (order_date + timedelta(minutes=random.randint(10, 120))).strftime('%Y-%m-%d %H:%M:%S'),
                    'order_delivered_carrier_date': (order_date + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),
                    'order_delivered_customer_date': (order_date + timedelta(days=random.randint(3, 14))).strftime('%Y-%m-%d %H:%M:%S'),
                    'order_estimated_delivery_date': (order_date + timedelta(days=18)).strftime('%Y-%m-%d %H:%M:%S')
                })

                # Order items (1-3 items per order)
                num_items = np.random.choice([1, 2, 3], p=[0.8, 0.15, 0.05])
                total_order_val = 0.0

                for item_idx in range(1, num_items + 1):
                    pid = random.choice(product_ids)
                    
                    # Price variation by channel/segment
                    base_price = float(np.random.lognormal(mean=4.3, sigma=0.8)) # ~ $70-150
                    if orig in ['email', 'paid_search']:
                        base_price *= 1.25 # higher AOV channels
                    
                    price = round(base_price, 2)
                    freight = round(max(8.5, price * random.uniform(0.08, 0.22)), 2)
                    total_order_val += (price + freight)

                    item_rows.append({
                        'order_id': order_id,
                        'order_item_id': item_idx,
                        'product_id': pid,
                        'seller_id': cs['seller_id'],
                        'shipping_limit_date': (order_date + timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S'),
                        'price': price,
                        'freight_value': freight
                    })

                # Order payments
                payment_rows.append({
                    'order_id': order_id,
                    'payment_sequential': 1,
                    'payment_type': np.random.choice(['credit_card', 'boleto', 'voucher', 'debit_card'], p=[0.75, 0.18, 0.04, 0.03]),
                    'payment_installments': random.randint(1, 8),
                    'payment_value': round(total_order_val, 2)
                })

                # Order reviews
                rev_score = int(np.random.choice([5, 4, 3, 2, 1], p=[0.58, 0.20, 0.10, 0.05, 0.07]))
                review_rows.append({
                    'review_id': make_hex_id(),
                    'order_id': order_id,
                    'review_score': rev_score,
                    'review_comment_title': 'Ótimo produto' if rev_score >= 4 else 'Atrasou a entrega',
                    'review_comment_message': 'Recomendo muito este vendedor!' if rev_score >= 4 else 'Demorou para responder.',
                    'review_creation_date': (order_date + timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S'),
                    'review_answer_timestamp': (order_date + timedelta(days=11)).strftime('%Y-%m-%d %H:%M:%S')
                })

    df_orders = pd.DataFrame(order_rows)
    df_items = pd.DataFrame(item_rows)
    df_payments = pd.DataFrame(payment_rows)
    df_reviews = pd.DataFrame(review_rows)

    df_orders.to_csv(os.path.join(output_dir, 'olist_orders_dataset.csv'), index=False)
    df_items.to_csv(os.path.join(output_dir, 'olist_order_items_dataset.csv'), index=False)
    df_payments.to_csv(os.path.join(output_dir, 'olist_order_payments_dataset.csv'), index=False)
    df_reviews.to_csv(os.path.join(output_dir, 'olist_order_reviews_dataset.csv'), index=False)

    print(f"  [OK] Orders saved: {len(df_orders)} orders, {len(df_items)} order items")
    print("Olist dataset generation completed successfully!")

if __name__ == '__main__':
    generate_olist_data()
