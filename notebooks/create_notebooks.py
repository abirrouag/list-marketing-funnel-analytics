"""
Creates executable Jupyter Notebooks (.ipynb) for:
1. 01_data_audit.ipynb
2. 02_funnel_and_time_to_close.ipynb
3. 03_revenue_by_origin.ipynb
"""

import os
import json

def make_notebook(cells, filename):
    nb = {
        "cells": cells,
        "metadata": {
            "language_info": {
                "name": "python",
                "version": "3.11"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    print(f"Created notebook: {filename}")

def build_all_notebooks(output_dir="notebooks"):
    os.makedirs(output_dir, exist_ok=True)

    # 1. 01_data_audit.ipynb
    cells_1 = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 01. Data Audit & Quality Reconciliation\n",
                "**Objective**: Audit raw Olist datasets for missing values, duplicate primary keys, date order sanity (`won_date >= first_contact_date`), orphan keys, and active seller counts."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import sys, os\n",
                "sys.path.insert(0, os.path.abspath('..'))\n",
                "from src.analytics import run_data_audit\n",
                "import pandas as pd\n",
                "\n",
                "# Run empirical data audit\n",
                "audit = run_data_audit('../data/raw')\n",
                "df_audit = pd.DataFrame(list(audit.items()), columns=['Audit Metric', 'Value'])\n",
                "df_audit"
            ]
        }
    ]
    make_notebook(cells_1, os.path.join(output_dir, "01_data_audit.ipynb"))

    # 2. 02_funnel_and_time_to_close.ipynb
    cells_2 = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 02. Funnel Conversion & Time-To-Close Survival Analysis\n",
                "**Objective**: Evaluate lead conversion rates by origin with Wilson 95% CIs, perform Chi-Square test of independence, and construct Kaplan-Meier survival curves treating unwon leads as right-censored."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import sys, os\n",
                "sys.path.insert(0, os.path.abspath('..'))\n",
                "from src.analytics import analyze_funnel_conversion, calculate_kaplan_meier_survival\n",
                "import pandas as pd\n",
                "\n",
                "df_funnel, chi_res = analyze_funnel_conversion('../data/processed')\n",
                "print('--- Chi-Square Test Results ---')\n",
                "print(chi_res)\n",
                "print('\\n--- Funnel Conversion with 95% Wilson CIs ---')\n",
                "df_funnel"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "km_res = calculate_kaplan_meier_survival('../data/processed')\n",
                "print('Log-Rank Test p-value:', km_res['log_rank_p_value'])\n",
                "df_medians = pd.DataFrame(list(km_res['median_days'].items()), columns=['Origin', 'Median Days to Close'])\n",
                "df_medians.sort_values(by='Median Days to Close')"
            ]
        }
    ]
    make_notebook(cells_2, os.path.join(output_dir, "02_funnel_and_time_to_close.ipynb"))

    # 3. 03_revenue_by_origin.ipynb
    cells_3 = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 03. Revenue Depth, Bootstrap CIs & Sensitivity Analysis\n",
                "**Objective**: Calculate 95% Bootstrap Confidence Intervals for revenue per closed deal, construct Segment x Origin heatmap matrix with n < 10 suppression, and evaluate sensitivity across 90d/180d/365d post-signing windows."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import sys, os\n",
                "sys.path.insert(0, os.path.abspath('..'))\n",
                "from src.analytics import calculate_revenue_bootstrap_and_heatmap, calculate_revenue_sensitivity\n",
                "\n",
                "df_boot, df_heatmap = calculate_revenue_bootstrap_and_heatmap('../data/processed')\n",
                "print('--- Bootstrap 95% CIs for Revenue per Closed Deal ---')\n",
                "df_boot"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "df_sens = calculate_revenue_sensitivity('../data/processed')\n",
                "print('--- Revenue Post-Signing Sensitivity Windows (90d vs 180d vs 365d) ---')\n",
                "df_sens"
            ]
        }
    ]
    make_notebook(cells_3, os.path.join(output_dir, "03_revenue_by_origin.ipynb"))

if __name__ == '__main__':
    build_all_notebooks()
