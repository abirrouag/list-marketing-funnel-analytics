"""
Plots Generator: Creates publication-quality static chart figures (PNG/SVG) for documentation,
notebooks, and Power BI screenshot visual placeholders.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.analytics import analyze_funnel_conversion, calculate_kaplan_meier_survival, calculate_revenue_bootstrap_and_heatmap

# Styling setup
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['axes.labelsize'] = 10

def generate_all_plots(docs_dir="docs", screenshots_dir="powerbi/screenshots"):
    """
    Generates static PNG charts for documentation and Power BI build guide.
    """
    os.makedirs(docs_dir, exist_ok=True)
    os.makedirs(screenshots_dir, exist_ok=True)

    print("[PLOTS] Generating publication-quality charts...")

    # 1. Funnel Conversion Rate with Wilson 95% Confidence Intervals
    df_funnel, _ = analyze_funnel_conversion()
    plt.figure(figsize=(10, 5))
    
    y_pos = np.arange(len(df_funnel))
    rates = df_funnel['conversion_rate'] * 100
    err_low = (df_funnel['conversion_rate'] - df_funnel['wilson_ci_lower']) * 100
    err_high = (df_funnel['wilson_ci_upper'] - df_funnel['conversion_rate']) * 100

    bars = plt.barh(y_pos, rates, xerr=[err_low, err_high], align='center', color='#3b82f6', alpha=0.85, capsize=5, ecolor='#1e3a8a')
    plt.yticks(y_pos, df_funnel['origin'].str.replace('_', ' ').str.title())
    plt.gca().invert_yaxis()  # top-down
    plt.xlabel('Conversion Rate (%) [with 95% Wilson CIs]')
    plt.title('MQL to Closed Deal Conversion Rate by Lead Origin')
    
    for bar in bars:
        width = bar.get_width()
        plt.text(width + 0.8, bar.get_y() + bar.get_height()/2, f'{width:.1f}%', va='center', fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(docs_dir, 'funnel_conversion_ci.png'), dpi=300)
    plt.savefig(os.path.join(screenshots_dir, '01_funnel_conversion_view.png'), dpi=300)
    plt.close()

    # 2. Kaplan-Meier Time-to-Close Survival Curves
    km_data = calculate_kaplan_meier_survival()
    plt.figure(figsize=(10, 5))
    
    colors = ['#1e40af', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#64748b', '#14b8a6', '#f97316']
    
    for idx, (orig, curve) in enumerate(km_data['survival_curves'].items()):
        if idx >= 6: break # Top 6 channels for legibility
        plt.step(curve['times'], curve['probabilities'], where='post', label=orig.replace('_', ' ').title(), color=colors[idx % len(colors)], linewidth=2)

    plt.xlabel('Days Since First Contact')
    plt.ylabel('Probability of Remaining Unwon (Survival S(t))')
    plt.title(f"Kaplan-Meier Time-To-Close Curves (Log-Rank p < 0.001)")
    plt.legend(loc='lower left', frameon=True)
    plt.grid(True, linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    plt.savefig(os.path.join(docs_dir, 'kaplan_meier_survival.png'), dpi=300)
    plt.savefig(os.path.join(screenshots_dir, '02_speed_survival_view.png'), dpi=300)
    plt.close()

    # 3. Revenue per Closed Deal with Bootstrap 95% CIs
    df_boot, _ = calculate_revenue_bootstrap_and_heatmap()
    plt.figure(figsize=(10, 5))

    y_pos = np.arange(len(df_boot))
    means = df_boot['mean_revenue_per_deal']
    err_low = df_boot['mean_revenue_per_deal'] - df_boot['boot_ci_lower']
    err_high = df_boot['boot_ci_upper'] - df_boot['mean_revenue_per_deal']

    bars = plt.barh(y_pos, means, xerr=[err_low, err_high], align='center', color='#10b981', alpha=0.85, capsize=5, ecolor='#065f46')
    plt.yticks(y_pos, df_boot['origin'].str.replace('_', ' ').str.title())
    plt.gca().invert_yaxis()
    plt.xlabel('Revenue Post-Signing per Closed Deal ($) [95% Bootstrap CIs]')
    plt.title('Post-Signing Monetization Depth by Acquisition Origin')

    for bar in bars:
        width = bar.get_width()
        plt.text(width + 15, bar.get_y() + bar.get_height()/2, f'${width:,.0f}', va='center', fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig(os.path.join(docs_dir, 'revenue_bootstrap_ci.png'), dpi=300)
    plt.savefig(os.path.join(screenshots_dir, '03_revenue_view.png'), dpi=300)
    plt.close()

    print("[PLOTS] Static figures generated and saved successfully!")

if __name__ == '__main__':
    generate_all_plots()
