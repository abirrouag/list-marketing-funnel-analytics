# PROJECT 3: Marketing Funnel & Revenue Analytics (BI)

> Agent brief. Read fully before acting. Work in the repo root. Follow "Working rules" at the bottom.

## 1. Business problem
Which lead channels (`origin`) and segments convert fastest and produce the most revenue **after signing**? Deliver decisions for a marketing team, not just charts.

## 2. Data (downloaded manually by the user into `data/raw/`)
**Olist Marketing Funnel** (Kaggle: "Marketing Funnel by Olist")
- `olist_marketing_qualified_leads_dataset.csv`: mql_id, first_contact_date, landing_page_id, origin
- `olist_closed_deals_dataset.csv`: mql_id, seller_id, sdr_id, sr_id, won_date, business_segment, lead_type, lead_behaviour_profile, has_company, has_gtin, average_stock, business_type, declared_product_catalog_size, declared_monthly_revenue

**Olist Brazilian E-Commerce** (Kaggle: "Brazilian E-Commerce Public Dataset by Olist")
- orders, order_items, order_payments, order_reviews, customers, sellers, products, product_category_name_translation (geolocation optional)

Link: `closed_deals.seller_id` -> `order_items.seller_id`; `closed_deals.mql_id` -> `mql.mql_id`.

## 3. Repo structure (create exactly)
```
data/raw/            # untouched CSVs (gitignored if large; keep a data/README.md with download steps)
data/processed/      # cleaned/exported tables for Power BI
sql/
  00_schema.sql      # star schema DDL
  01_load.sql        # COPY / staging -> dims/facts
  02_funnel_conversion.sql
  03_time_to_close.sql
  04_seller_revenue_by_origin.sql
  05_cohort_revenue.sql
  06_powerbi_views.sql
notebooks/
  01_data_audit.ipynb
  02_funnel_and_time_to_close.ipynb
  03_revenue_by_origin.ipynb
powerbi/
  measures.dax       # all DAX measures, commented
  build_guide.md     # click-by-click Power BI Desktop build steps
  screenshots/       # filled by the user after building
docs/
  schema.md          # Mermaid ERD + table grain descriptions
  schema.png         # rendered ERD
  recommendations.md # ONE-PAGE memo (the key deliverable)
src/                 # load_data.py, db.py, plots.py
docker-compose.yml   # postgres:16
requirements.txt
.env.example
README.md
```

## 4. Tasks

### 4.1 Environment
- `docker-compose.yml` with Postgres 16, a named volume, credentials from `.env`.
- `src/load_data.py`: loads CSVs into a `staging` schema using pandas + SQLAlchemy/psycopg. Idempotent (can be re-run).

### 4.2 Star schema (schema `dw`)
Design two fact tables that share conformed dimensions:
- `fact_lead` (grain: one row per MQL): mql_id, date_key_first_contact, origin_key, landing_page_key, is_won (0/1), date_key_won (nullable), days_to_close (nullable), seller_key (nullable), segment_key, sdr_key, sr_key
- `fact_order_item` (grain: one row per order item): order_id, order_item_id, date_key_purchase, seller_key, product_key, customer_key, price, freight_value, order_status, review_score, days_after_won (nullable, purchase date minus won_date for that seller)
- Dimensions: `dim_date`, `dim_origin`, `dim_landing_page`, `dim_seller` (with won_date, lead_type, behaviour_profile, business_type, declared revenue/catalog size), `dim_segment`, `dim_sdr`, `dim_sr`, `dim_product` (English category), `dim_customer` (state/city).
- Use surrogate keys, primary/foreign keys, indexes on join columns, and NOT NULL/CHECK constraints where sensible. Handle NULL origin explicitly as `'unknown'`.
- Produce `docs/schema.md` with a Mermaid `erDiagram` and grain statements, and render `docs/schema.png` (mermaid-cli if available, otherwise matplotlib/graphviz fallback).

### 4.3 SQL analysis (each file commented with the question it answers)
1. **Funnel conversion** by origin, landing page, and month of first contact: MQLs, closed deals, conversion rate, with Wilson 95% intervals (compute in Python if awkward in SQL).
2. **Time-to-close**: days between first_contact_date and won_date; median, p75, p90 by origin and by segment (`percentile_cont`). Include closed deals only, and state the right-censoring problem for open leads.
3. **Seller revenue by lead origin**: revenue, orders, average order value, review score, freight share, only for order items **on/after won_date**. Also revenue per closed deal (not just per active seller).
4. **Activation**: share of closed sellers with at least one order after signing, and time from won_date to first order, by origin.
5. **Cohort view**: cumulative revenue by months since signing, by origin.
6. Window functions: rank origins by revenue per deal; running totals.
7. Views in `06_powerbi_views.sql` that the Power BI model can consume directly.

### 4.4 Python depth (notebooks)
- Data audit: nulls, duplicates, date sanity (won_date >= first_contact_date), orphan keys, how many closed sellers appear in orders. **Report the real numbers; do not assume them.**
- Funnel: conversion by origin with confidence intervals; chi-square test of independence for origin vs won.
- Time-to-close: Kaplan-Meier curves by origin (lifelines) treating unwon leads as censored, log-rank test.
- Revenue: bootstrap CIs for revenue per closed deal by origin; segment x origin heatmap with a minimum-sample-size rule (suppress cells with n < 10).
- Sensitivity: how conclusions change if the revenue window is 90/180/365 days after signing.
- Save clean tables to `data/processed/` for Power BI.

### 4.5 Power BI (agent prepares; the user builds in Power BI Desktop)
The agent cannot produce a .pbix file. Instead produce:
- `powerbi/measures.dax` with commented measures, e.g. `MQLs`, `Closed Deals`, `Conversion Rate`, `Median Days To Close`, `Revenue Post-Signing`, `Revenue per Closed Deal`, `Activation Rate`, `Avg Review Score`, `Conversion Rate vs Overall` (using CALCULATE/ALL/DIVIDE), time-intelligence measures, and a dynamic segment/origin ranking with RANKX.
- `powerbi/build_guide.md`: connect to Postgres, import the views, model relationships (single-direction, star), mark date table, page-by-page layout (1. Funnel, 2. Speed, 3. Revenue, 4. Seller drill-through), slicers, tooltips, bookmarks, and the screenshot checklist.

### 4.6 Recommendation memo (`docs/recommendations.md`)
One page (~400-500 words), structure: **Headline recommendation -> Evidence (3 numbers) -> Actions by channel -> Expected impact -> Risks/caveats -> Next test.** Every number must come from the analysis outputs; cite the notebook/SQL file it came from. Write for a marketing lead: decisions first, method last. Include a short "What I would A/B test next".

## 5. Acceptance criteria
- `docker compose up -d` then `python src/load_data.py` builds the warehouse from scratch with no manual SQL edits.
- All SQL files run in order without errors; row counts reconciled and logged.
- Schema diagram present; DAX file and build guide present; memo present with real numbers.
- README: problem, data, how to run, key findings (3 bullets), schema image, limitations.

## 6. Working rules
- Ask before installing anything outside `requirements.txt`/Docker. Never commit raw data or `.env`.
- Never invent numbers or results. If something can't be run, say so and leave a clearly marked TODO.
- Plan first: list the steps, then execute phase by phase (4.1 -> 4.6), running and verifying each phase before the next.
- Keep code readable: docstrings, typed functions, no hard-coded paths.
