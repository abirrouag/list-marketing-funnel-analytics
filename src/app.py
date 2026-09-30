"""
FastAPI Server for Interactive SaaS BI & Marketing Analytics Dashboard.
Serves REST API endpoints and static frontend dashboard assets.
"""

import os
import sys
import math
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy import text

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.db import get_engine
from src.analytics import (
    run_data_audit,
    analyze_funnel_conversion,
    calculate_kaplan_meier_survival,
    calculate_revenue_bootstrap_and_heatmap,
    calculate_revenue_sensitivity,
    generate_channel_recommendations,
    detect_channel_anomalies,
    simulate_budget_reallocation
)

app = FastAPI(
    title="Olist Marketing Funnel & Revenue Analytics Engine",
    description="SaaS BI Intelligence Platform for Channel ROI & Seller Performance",
    version="1.1.0"
)

PROCESSED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/processed'))
RAW_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/raw'))


def sanitize_nans(val):
    """
    Recursively replaces NaN, Infinity, and -Infinity values with None for clean JSON compliance.
    """
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return None
        return val
    elif isinstance(val, dict):
        return {k: sanitize_nans(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [sanitize_nans(v) for v in val]
    return val


# Pydantic Schema for Budget Simulation Request
class BudgetSimulationRequest(BaseModel):
    budget_changes: dict  # e.g. {"paid_search": 20, "social": -30}


@app.get("/api/overview")
def get_overview():
    """
    Returns executive KPI cards and high-level summary metrics.
    """
    engine = get_engine()
    df_perf = pd.read_sql("SELECT * FROM vw_powerbi_channel_matrix", engine)

    total_mqls = int(df_perf['total_mqls'].sum())
    total_closed = int(df_perf['closed_deals'].sum())
    overall_conv = round(total_closed / total_mqls, 4) if total_mqls > 0 else 0.0

    total_revenue = float(df_perf['total_post_signing_revenue'].sum())
    avg_rev_per_deal = round(total_revenue / total_closed, 2) if total_closed > 0 else 0.0

    total_active_sellers = int(df_perf['active_sellers'].sum())
    overall_activation = round(total_active_sellers / total_closed, 4) if total_closed > 0 else 0.0

    avg_days_close = round(float(df_perf['avg_days_to_close'].mean()), 1)

    payload = {
        "total_mqls": total_mqls,
        "total_closed_deals": total_closed,
        "overall_conversion_rate": overall_conv,
        "total_post_signing_revenue": round(total_revenue, 2),
        "revenue_per_closed_deal": avg_rev_per_deal,
        "active_sellers": total_active_sellers,
        "activation_rate": overall_activation,
        "avg_days_to_close": avg_days_close
    }
    return sanitize_nans(payload)


@app.get("/api/roi")
def get_channel_roi_analysis():
    """
    Returns Executive Channel ROI & CAC Efficiency Index metrics.
    CAC baseline estimates: Paid Search: $45, Referral: $20, Organic Search: $15, Direct: $10, Email: $12, Social: $35, Display: $40
    """
    engine = get_engine()
    df_perf = pd.read_sql("SELECT * FROM vw_powerbi_channel_matrix", engine)

    base_cac = {
        'paid_search': 45.0,
        'referral': 20.0,
        'organic_search': 15.0,
        'direct_traffic': 10.0,
        'email': 12.0,
        'social': 35.0,
        'organic_social': 18.0,
        'display': 40.0,
        'other': 30.0,
        'unknown': 25.0
    }

    roi_rows = []

    for _, row in df_perf.iterrows():
        orig = row['lead_origin']
        mqls = row['total_mqls']
        deals = row['closed_deals']
        rev_deal = row['revenue_per_closed_deal']
        total_rev = row['total_post_signing_revenue']

        cac = base_cac.get(orig, 25.0)
        total_est_cost = mqls * cac
        net_profit = total_rev - total_est_cost
        roi_ratio = round(total_rev / total_est_cost, 2) if total_est_cost > 0 else 0.0
        payback_months = round((cac / (rev_deal / 12)), 1) if rev_deal > 0 else 0.0

        roi_rows.append({
            'origin': orig,
            'total_mqls': mqls,
            'closed_deals': deals,
            'est_cac': cac,
            'total_estimated_spend': round(total_est_cost, 2),
            'total_post_signing_revenue': round(total_rev, 2),
            'net_profit': round(net_profit, 2),
            'roi_multiple': roi_ratio,
            'payback_months': payback_months
        })

    df_roi = pd.DataFrame(roi_rows).sort_values(by='roi_multiple', ascending=False)
    return sanitize_nans(df_roi.replace({np.nan: None}).to_dict(orient="records"))


@app.get("/api/segments")
def get_segment_revenue_distribution():
    """
    Returns seller business segment performance distribution.
    """
    engine = get_engine()
    query = """
        SELECT 
            seg.segment_name,
            COUNT(DISTINCT sel.seller_key) AS closed_sellers,
            COALESCE(SUM(foi.price), 0.0) AS total_revenue,
            COALESCE(COUNT(DISTINCT foi.order_id), 0) AS total_orders,
            COALESCE(ROUND(AVG(foi.review_score), 2), 0.0) AS avg_review_score
        FROM dim_segment seg
        JOIN fact_lead fl ON seg.segment_key = fl.segment_key
        LEFT JOIN dim_seller sel ON fl.seller_key = sel.seller_key
        LEFT JOIN fact_order_item foi ON sel.seller_key = foi.seller_key AND foi.days_after_won >= 0
        GROUP BY seg.segment_name
        ORDER BY total_revenue DESC
    """
    df = pd.read_sql(query, engine)
    return sanitize_nans(df.replace({np.nan: None}).to_dict(orient="records"))


@app.get("/api/funnel")
def get_funnel_analysis():
    """
    Returns funnel conversion data, Wilson 95% CIs, and Chi-Square statistical test results.
    """
    df_funnel, chi_res = analyze_funnel_conversion(PROCESSED_DIR)
    payload = {
        "funnel_data": df_funnel.replace({np.nan: None}).to_dict(orient="records"),
        "chi_square_test": chi_res
    }
    return sanitize_nans(payload)


@app.get("/api/speed")
def get_speed_survival():
    """
    Returns Kaplan-Meier survival curves and Log-Rank test statistics.
    """
    km_res = calculate_kaplan_meier_survival(PROCESSED_DIR)
    return sanitize_nans(km_res)


@app.get("/api/revenue")
def get_revenue_analytics():
    """
    Returns Bootstrap 95% CIs for revenue per deal, Segment x Origin heatmap, and sensitivity windows.
    """
    df_boot, df_heatmap = calculate_revenue_bootstrap_and_heatmap(PROCESSED_DIR)
    df_sens = calculate_revenue_sensitivity(PROCESSED_DIR)

    payload = {
        "bootstrap_cis": df_boot.replace({np.nan: None}).to_dict(orient="records"),
        "heatmap_matrix": df_heatmap.replace({np.nan: None}).to_dict(orient="records"),
        "sensitivity_windows": df_sens.replace({np.nan: None}).to_dict(orient="records")
    }
    return sanitize_nans(payload)


@app.get("/api/recommendations")
def get_recommendations():
    """
    Returns Strategic Channel Recommendations (Clever Feature #1).
    """
    df_recs = generate_channel_recommendations(PROCESSED_DIR)
    payload = df_recs.replace({np.nan: None}).to_dict(orient="records")
    return sanitize_nans(payload)


@app.get("/api/anomalies")
def get_anomalies():
    """
    Returns Automatic Anomaly & Risk Alerts (Clever Feature #2).
    """
    anomalies = detect_channel_anomalies(PROCESSED_DIR)
    return sanitize_nans(anomalies)


@app.post("/api/simulate")
def run_simulation(req: BudgetSimulationRequest):
    """
    Simulates budget reallocation impact on MQLs, deals, revenue, and ROI (Clever Feature #3).
    """
    sim_res = simulate_budget_reallocation(req.budget_changes, PROCESSED_DIR)
    return sanitize_nans(sim_res)


@app.get("/api/audit")
def get_audit_report():
    """
    Returns data audit & reconciliation metrics.
    """
    audit = run_data_audit(RAW_DIR)
    return sanitize_nans(audit)


@app.get("/api/data/leads")
def get_fact_leads_data(limit: int = 100):
    """
    Returns raw fact lead table for Data Explorer.
    """
    engine = get_engine()
    query = """
        SELECT fl.lead_key, fl.mql_id, o.origin_name, lp.landing_page_id, fl.is_won, fl.days_to_close
        FROM fact_lead fl
        JOIN dim_origin o ON fl.origin_key = o.origin_key
        JOIN dim_landing_page lp ON fl.landing_page_key = lp.landing_page_key
        LIMIT :lim
    """
    df = pd.read_sql(text(query), engine, params={"lim": limit})
    payload = df.replace({np.nan: None}).to_dict(orient="records")
    return sanitize_nans(payload)


# Serve static web frontend
web_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../web'))
if os.path.exists(web_dir):
    app.mount("/static", StaticFiles(directory=web_dir), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(os.path.join(web_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
