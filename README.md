# SaaS KPI Dashboard

> Tracked executive-level business performance across revenue, churn, and profitability for a simulated SaaS business with 10,000 customers — surfacing that SMB drives 61% of total revenue despite having the highest churn risk, and that gross margins held above 93% consistently across 36 months.

![SQL](https://img.shields.io/badge/SQL-PostgreSQL-blue)
![PowerBI](https://img.shields.io/badge/Dashboard-PowerBI-yellow)
![Python](https://img.shields.io/badge/Data-Python-green)

---

## Dashboard

![KPI Dashboard](reports/dashboard_page1.png)

---

## Key Business Findings

- **$11.43M total revenue** generated across Jan 2022 — Dec 2024, growing from ~$50K/month to $603K/month
- **SMB segment drives 61% of revenue** ($6.7M) despite churning at the highest rate — concentrated risk
- **Gross margin consistently above 93%** across all 36 months — healthy unit economics
- **Average monthly churn rate: 1.05%** — translates to ~12.6% annual churn, above SaaS benchmark of 5–7%
- **MoM revenue growth:** mostly positive with occasional dips — Nov 2024 saw a -0.69% dip, recovered to +6.0% in Dec 2024
- **8,066 paying customers** as of Dec 2024 — up from near zero in Jan 2022

**Business recommendation:** The SMB segment is both the largest revenue driver and the highest churn risk. Reducing SMB churn by 3% annually would retain approximately $200K in recurring revenue — priority retention investment should target this segment first.

---

## SQL Analysis

All KPIs computed via SQL on a PostgreSQL database, exported to CSV for dashboard consumption.

### Revenue by Segment
| Segment | Total Revenue | Customers | Revenue per Customer |
|---|---|---|---|
| SMB | $6,697,554 | 6,020 | $1,112 |
| Mid-Market | $2,945,493 | 2,450 | $1,202 |
| Enterprise | $1,786,584 | 1,472 | $1,214 |

### Recent Monthly Performance
| Month | Revenue | Paying Customers | MoM Growth |
|---|---|---|---|
| Dec 2024 | $603,627 | 8,066 | +6.00% |
| Nov 2024 | $569,481 | 7,855 | -0.69% |
| Oct 2024 | $573,441 | 7,681 | +5.85% |

### Gross Margin (Recent)
| Month | Revenue | Total Costs | Gross Profit | Margin |
|---|---|---|---|---|
| Dec 2024 | $603,627 | $35,151 | $568,476 | 94.18% |
| Nov 2024 | $569,481 | $34,648 | $534,833 | 93.92% |
| Oct 2024 | $573,441 | $31,963 | $541,478 | 94.43% |

---

## Dashboard Pages

**Executive Overview** — 4 KPI tiles (Total Revenue, Avg Churn Rate, Conversion Rate, Gross Margin), Monthly Revenue Trend, Monthly Churn Rate, Revenue by Segment

---

## SQL Modules

| File | What it computes |
|---|---|
| `kpi.sql` | Monthly revenue, paying customers, churn rate, conversion rate |
| `forecast.sql` | 3–6 month revenue projections |
| `anomaly_detection.sql` | Flags months with >10–15% MoM revenue changes |
| `db_setup.sql` | Schema setup and table creation |

---

## Project Structure
```
kpi_dashboard/
│
├── dashboard_data/csv/         # Pre-aggregated SQL output
│   ├── monthly_revenue.csv
│   ├── churn_rate.csv
│   ├── gross_margin.csv
│   ├── mom_growth.csv
│   ├── revenue_by_segment.csv
│   ├── revenue_anomalies.csv
│   ├── revenue_forecast.csv
│   ├── churn_spike_detection.csv
│   └── conversion_rate.csv
├── reports/
│   └── dashboard_page1.png     # Executive dashboard
├── kpi.sql
├── forecast.sql
├── anomaly_detection.sql
├── db_setup.sql
├── generate_saas_data.py
├── customers.csv
├── subscriptions.csv
├── payments.csv
├── costs.csv
└── README.md
```

---

## Run Locally

### Generate data
```bash
pip install -r requirements.txt
python generate_saas_data.py
```

### Run SQL analysis
Load CSVs into PostgreSQL using `db_setup.sql`, then run `kpi.sql`, `forecast.sql`, and `anomaly_detection.sql`.



## Tech Stack

| Layer | Tools |
|---|---|
| Data Generation | Python, Faker |
| Database | PostgreSQL |
| Analysis | SQL |
| Dashboard | Power BI |
| Language | Python 3.9+ |