# Power BI Desktop Implementation & Build Guide

> **Project**: Marketing Funnel & Revenue Analytics (Olist Data Warehouse)  
> **Target Audience**: Business Intelligence Analysts, Marketing VP, Sales Operations  

---

## 1. Data Connection & Import Setup

1. Open **Power BI Desktop**.
2. Select **Get Data** -> **PostgreSQL Database** (or **Folder / CSV** pointing to `data/processed/`).
   - Server: `localhost:5432`
   - Database: `olist_dw`
   - Import Mode: **Import** (Recommended for analytical calculations)
3. Select the analytical pre-built views:
   - `vw_powerbi_funnel_conversion`
   - `vw_powerbi_time_to_close`
   - `vw_powerbi_seller_post_signing`
   - `vw_powerbi_cohort_revenue`
   - `vw_powerbi_channel_matrix`
   - `dim_origin`
   - `dim_date`
   - `dim_seller`

---

## 2. Data Modeling & Star Schema Relationships

Ensure single-direction 1-to-many relationships are established:

* `dim_origin[origin_name]` `1` ---- `*` `vw_powerbi_funnel_conversion[lead_origin]`
* `dim_origin[origin_name]` `1` ---- `*` `vw_powerbi_channel_matrix[lead_origin]`
* `dim_date[date_key]` `1` ---- `*` `fact_lead[date_key_first_contact]`
* Mark `dim_date` as official **Date Table** (`full_date` column).

---

## 3. DAX Measures Integration

1. In Power BI Desktop, create a dedicated table named `_Measures`.
2. Open `powerbi/measures.dax` and paste each measure into the `_Measures` container table.
3. Apply standard formatting:
   - `Conversion Rate`, `Activation Rate`: **Percentage** (`0.0%`)
   - `Revenue Post-Signing`, `Revenue per Closed Deal`, `Average Order Value`: **Currency ($)** (`$#,##0.00`)
   - `Median Days To Close`: **Whole Number**

---

## 4. Page-by-Page Layout Architecture

### Page 1: Executive Funnel & Conversion Matrix
* **KPI Cards (Top Bar)**:
  - `MQLs` | `Closed Deals` | `Conversion Rate` | `Overall Benchmark Conversion`
* **Visual 1 (Horizontal Bar Chart)**:
  - Axis: `dim_origin[origin_name]`
  - Values: `Conversion Rate`
  - Error Bars: Lower = `Wilson CI Lower`, Upper = `Wilson CI Upper`
* **Visual 2 (Clustered Column Chart)**:
  - Shared Axis: `dim_date[month_name]`
  - Series: `MQLs`, `Closed Deals`
* **Slicers**: Date range, Lead Origin, Landing Page ID.

### Page 2: Speed & Time-To-Close Analysis
* **KPI Cards**:
  - `Median Days To Close` | `P75 Days To Close` | `Avg Days To First Order`
* **Visual 1 (Scatter Plot / Speed Matrix)**:
  - X-Axis: `Median Days To Close`
  - Y-Axis: `Conversion Rate`
  - Bubble Size: `Closed Deals`
* **Visual 2 (Decomposition Tree)**:
  - Analyze: `Median Days To Close`
  - Explain by: `Lead Origin`, `Business Segment`, `SDR ID`

### Page 3: Revenue Depth & Cohort Ramp-Up
* **KPI Cards**:
  - `Revenue Post-Signing` | `Revenue per Closed Deal` | `Activation Rate` | `Avg Review Score`
* **Visual 1 (Heatmap Matrix)**:
  - Rows: `Business Segment`
  - Columns: `Lead Origin`
  - Values: `Revenue per Closed Deal`
  - Conditional Formatting: Color scale based on value ($0 = light gray).
* **Visual 2 (Stacked Area Chart - Cohort Ramp-up)**:
  - Axis: `Months Since Signing` (0 to 12)
  - Legend: `Lead Origin`
  - Values: `Cumulative Cohort Revenue`

### Page 4: Seller Drill-Through Matrix
* **Target Table**: `vw_powerbi_seller_post_signing`
* Drill-through enabled on `seller_id` from Page 1, 2, and 3.
* Displays individual seller firmographics, declared revenue, catalog size, won date, post-signing order items, and customer review scores.

---

## 5. Screenshot Checklist

- [x] Page 1: Funnel & Wilson 95% CIs View -> `powerbi/screenshots/01_funnel_conversion_view.png`
- [x] Page 2: Time-to-Close Speed & Survival Matrix -> `powerbi/screenshots/02_speed_survival_view.png`
- [x] Page 3: Post-Signing Revenue & Cohort View -> `powerbi/screenshots/03_revenue_view.png`
