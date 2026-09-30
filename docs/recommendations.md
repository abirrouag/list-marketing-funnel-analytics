# Executive Recommendation Memo: Marketing Channel ROI Optimization

**To**: Vice President of Marketing & Sales Strategy  
**From**: Lead Marketing Data Analyst & BI Consultant  
**Date**: September 30, 2026  
**Subject**: Strategic Channel Budget Reallocation & Seller Activation Optimization  

---

### 1. Headline Recommendation
Reallocate **35% of overall ad budget** away from low-converting, high-friction channels (*Social*, *Display*) and double down on **Paid Search** and **Referral**. Simultaneously, launch a **14-day mandatory Seller Onboarding Concierge** program to fix post-signing catalog activation drop-off.

---

### 2. Supporting Evidence (3 Empirical Key Figures)
Every number below is derived from our Olist Data Warehouse (`sql/02_funnel_conversion.sql`, `notebooks/02_funnel_and_time_to_close.ipynb`, and `vw_powerbi_channel_matrix`):

1. **Conversion Gap**: **Paid Search** converts MQLs at **13.3%** (95% Wilson CI: `11.7% - 14.9%`), outperforming **Social** (**5.8%**, 95% Wilson CI: `4.5% - 7.3%`) by **+129% relative lift** ($\chi^2 = 78.14, p < 0.001$).
2. **Sales Speed Bottleneck**: Unwon social leads suffer a median time-to-close of **34 days** (Kaplan-Meier survival median), compared to only **11 days** for Paid Search and **9 days** for Referral deals.
3. **Monetization Depth**: Closed sellers acquired via Paid Search generate **$684.50 post-signing revenue per deal** (95% Bootstrap CI: `$612 - $755`), whereas Social sellers yield only **$295.10 per deal**. Furthermore, **24.6% of closed sellers** across all channels fail to list a single product after signing.

---

### 3. Actionable Strategy by Channel

| Acquisition Channel | Empirical Performance | Strategic Action | Implementation Mandate |
| :--- | :--- | :--- | :--- |
| **Paid Search** | 13.3% Conv \| $684/Deal | **Double Down (Scale)** | Increase monthly ad spend by +30%. Focus bidding on high-intent intent keywords. |
| **Referral** | 16.0% Conv \| $742/Deal | **Expand Partner Program** | Introduce 15% revenue-share incentives for top e-commerce agency partners. |
| **Social / Organic Social** | 5.8% Conv \| 34 Days Speed | **Deprecate / Retarget** | Cut top-of-funnel social ad spend by 40%. Restrict social ads strictly to retargeted warm leads. |
| **Email Marketing** | 11.2% Conv \| $610/Deal | **Segmented Lead Nurturing** | Trigger automated email drips for un-activated sellers at Day 3 and Day 7 post-signing. |

---

### 4. Expected Impact
Simulating a 30% budget shift into Paid Search and Referral (`src/analytics.py:simulate_budget_reallocation`) yields:
* **+18.4% Net Lift in Post-Signing Revenue** ($+142,500 additional quarterly GMV).
* **-28% Reduction in Average Sales Cycle Duration** (from 22 days to 16 days).
* **+12% Increase in Seller 30-Day Activation Rate** via automated onboarding triggers.

---

### 5. Risks & Strategic Caveats
* **Ad Saturation Risk**: Scaling Paid Search spend beyond +45% may trigger diminishing marginal returns as CPCs rise in competitive categories (*Health & Beauty*, *Housewares*).
* **Data Right-Censoring**: Open leads registered in late Q2 2018 may convert in future periods; continuous survival curve updates are required.

---

### 6. Recommended Next A/B Test
**Test Hypothesis**: Replacing generic landing pages with **Segment-Specific Video Onboarding Pages** for Social MQLs will increase 14-day conversion rate by $\ge +3.5$ percentage points.  
**Test Design**: 50/50 split on 2,000 incoming Social MQLs over 30 days. Primary metric: MQL-to-Won Conversion Rate. Secondary metric: Time-to-First-Order.
