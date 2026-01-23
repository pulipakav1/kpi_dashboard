# End-to-End Business KPI Dashboard

## Project Overview

Build an executive KPI dashboard to track business performance across revenue, conversion, retention, and churn, including trend analysis, forecasting, and anomaly detection to support leadership decision-making.

## Data Generation

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Generate the dataset:
```bash
python generate_saas_data.py
```

This will create 4 CSV files:
- `customers.csv` - Customer master data
- `subscriptions.csv` - Subscription records
- `payments.csv` - Payment transactions
- `costs.csv` - Monthly cost breakdowns

### Data Schema

#### customers.csv
- `customer_id` (STRING) - Unique customer identifier
- `signup_date` (DATE) - Customer signup date
- `segment` (STRING) - SMB / Mid-Market / Enterprise
- `country` (STRING) - Country code
- `acquisition_channel` (STRING) - Paid Ads / Referral / Organic / Partner
- `is_active` (BOOLEAN) - Current active status

#### subscriptions.csv
- `subscription_id` (STRING) - Unique subscription identifier
- `customer_id` (STRING) - Linked customer
- `plan_type` (STRING) - Basic / Pro / Enterprise
- `start_date` (DATE) - Subscription start date
- `end_date` (DATE / NULL) - Cancellation date (NULL if active)
- `monthly_price` (DECIMAL) - Monthly subscription price

#### payments.csv
- `payment_id` (STRING) - Unique payment identifier
- `customer_id` (STRING) - Linked customer
- `payment_date` (DATE) - Payment date
- `amount` (DECIMAL) - Payment amount
- `payment_status` (STRING) - Success / Failed

#### costs.csv
- `month` (STRING) - YYYY-MM format
- `infra_cost` (DECIMAL) - Infrastructure costs
- `marketing_cost` (DECIMAL) - Marketing spend
- `support_cost` (DECIMAL) - Customer support costs

## Key Features

### Core KPIs
1. **Revenue** - Total subscription revenue per month
2. **Conversion Rate** - % of trial users who converted to paid
3. **Retention Rate** - % of customers retained month-over-month
4. **Churn Rate** - % of customers who canceled subscriptions

### Advanced Features
- **Forecasting** - 3-6 month revenue projections
- **Financial Analysis** - MoM/YoY growth, gross margin
- **Anomaly Detection** - Flag months with >10-15% revenue changes

## Dashboard Pages

1. **Executive Overview** - Revenue trends, churn & retention, KPI tiles, forecast overlay
2. **Customer Insights** - Churn by segment, conversion by geography, retention cohorts
3. **Financial Health** - Cost vs revenue, gross margin trends, profitability
