# export queries
import pandas as pd
import psycopg2
import os
from datetime import datetime

# db config
try:
    from config import DB_CONFIG
except ImportError:
    print("Error: config.py not found!")
    print("Copy config_template.py to config.py and add your database credentials")
    print("config.py is in .gitignore and won't be committed")
    exit(1)

# queries
QUERIES = {
    'monthly_revenue': """
        SELECT 
            DATE_TRUNC('month', payment_date) AS month,
            SUM(amount) AS monthly_revenue,
            COUNT(DISTINCT customer_id) AS paying_customers
        FROM payments
        WHERE payment_status = 'Success'
        GROUP BY DATE_TRUNC('month', payment_date)
        ORDER BY month DESC;
    """,
    
    'churn_rate': """
        WITH monthly_churned AS (
            SELECT 
                DATE_TRUNC('month', end_date) AS month,
                COUNT(DISTINCT customer_id) AS churned_customers
            FROM subscriptions
            WHERE end_date IS NOT NULL
            GROUP BY DATE_TRUNC('month', end_date)
        ),
        monthly_active AS (
            SELECT 
                DATE_TRUNC('month', payment_date) AS month,
                COUNT(DISTINCT customer_id) AS active_customers
            FROM payments
            WHERE payment_status = 'Success'
            GROUP BY DATE_TRUNC('month', payment_date)
        )
        SELECT 
            COALESCE(ma.month, mch.month) AS month,
            COALESCE(ma.active_customers, 0) AS active_customers,
            COALESCE(mch.churned_customers, 0) AS churned_customers,
            CASE 
                WHEN COALESCE(ma.active_customers, 0) > 0 
                THEN ROUND((COALESCE(mch.churned_customers, 0)::DECIMAL / 
                           (COALESCE(ma.active_customers, 0) + COALESCE(mch.churned_customers, 0))) * 100, 2)
                ELSE 0 
            END AS churn_rate_pct
        FROM monthly_active ma
        FULL OUTER JOIN monthly_churned mch ON ma.month = mch.month
        ORDER BY month DESC;
    """,
    
    'revenue_by_segment': """
        SELECT 
            c.segment,
            SUM(p.amount) AS total_revenue,
            COUNT(DISTINCT p.customer_id) AS customers
        FROM payments p
        JOIN customers c ON p.customer_id = c.customer_id
        WHERE p.payment_status = 'Success'
        GROUP BY c.segment;
    """,
    
    'conversion_rate': """
        SELECT 
            DATE_TRUNC('month', c.signup_date) AS month,
            COUNT(DISTINCT c.customer_id) AS total_signups,
            COUNT(DISTINCT s.customer_id) AS converted_customers,
            ROUND(
                (COUNT(DISTINCT s.customer_id)::DECIMAL / 
                 NULLIF(COUNT(DISTINCT c.customer_id), 0)) * 100, 
                2
            ) AS conversion_rate_pct
        FROM customers c
        LEFT JOIN subscriptions s ON c.customer_id = s.customer_id
        GROUP BY DATE_TRUNC('month', c.signup_date)
        ORDER BY month DESC;
    """,
    
    'mom_growth': """
        WITH monthly_revenue AS (
            SELECT 
                DATE_TRUNC('month', payment_date) AS month,
                SUM(amount) AS revenue
            FROM payments
            WHERE payment_status = 'Success'
            GROUP BY DATE_TRUNC('month', payment_date)
        )
        SELECT 
            month,
            revenue,
            LAG(revenue) OVER (ORDER BY month) AS previous_month_revenue,
            ROUND(
                ((revenue - LAG(revenue) OVER (ORDER BY month))::DECIMAL / 
                 NULLIF(LAG(revenue) OVER (ORDER BY month), 0)) * 100, 
                2
            ) AS mom_growth_pct
        FROM monthly_revenue
        ORDER BY month DESC;
    """,
    
    'gross_margin': """
        SELECT 
            c.month,
            COALESCE(SUM(p.amount), 0) AS revenue,
            (c.infra_cost + c.marketing_cost + c.support_cost) AS total_costs,
            COALESCE(SUM(p.amount), 0) - (c.infra_cost + c.marketing_cost + c.support_cost) AS gross_profit,
            ROUND(
                ((COALESCE(SUM(p.amount), 0) - (c.infra_cost + c.marketing_cost + c.support_cost))::DECIMAL / 
                 NULLIF(COALESCE(SUM(p.amount), 0), 0)) * 100, 
                2
            ) AS gross_margin_pct
        FROM costs c
        LEFT JOIN payments p 
            ON DATE_TRUNC('month', p.payment_date) = TO_DATE(c.month || '-01', 'YYYY-MM-DD')
            AND p.payment_status = 'Success'
        GROUP BY c.month, c.infra_cost, c.marketing_cost, c.support_cost
        ORDER BY c.month DESC;
    """,
    
    # forecast
    'revenue_forecast': """
        WITH monthly_revenue AS (
            SELECT 
                DATE_TRUNC('month', payment_date) AS month,
                SUM(amount) AS revenue
            FROM payments
            WHERE payment_status = 'Success'
            GROUP BY DATE_TRUNC('month', payment_date)
        ),
        historical AS (
            SELECT 
                month,
                revenue,
                AVG(revenue) OVER (
                    ORDER BY month 
                    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
                ) AS ma_3month,
                AVG(revenue) OVER (
                    ORDER BY month 
                    ROWS BETWEEN 5 PRECEDING AND CURRENT ROW
                ) AS ma_6month
            FROM monthly_revenue
        ),
        latest AS (
            SELECT 
                month,
                revenue,
                ma_3month,
                ma_6month,
                revenue - LAG(revenue, 1) OVER (ORDER BY month) AS mom_change
            FROM historical
            WHERE month = (SELECT MAX(month) FROM historical)
        ),
        forecast AS (
            SELECT 
                generate_series(1, 6) AS forecast_period,
                l.month + (INTERVAL '1 month' * generate_series(1, 6)) AS forecast_month,
                (l.ma_3month + GREATEST(0, l.revenue + (l.mom_change * generate_series(1, 6)))) / 2 AS forecasted_revenue
            FROM latest l
        )
        SELECT 
            'Historical' AS data_type,
            h.month AS period,
            h.revenue AS value
        FROM historical h
        WHERE h.month >= (SELECT MAX(month) - INTERVAL '12 months' FROM historical)
        UNION ALL
        SELECT 
            'Forecast' AS data_type,
            f.forecast_month AS period,
            f.forecasted_revenue AS value
        FROM forecast f
        ORDER BY data_type DESC, period;
    """,
    
    # anomalies
    'revenue_anomalies': """
        WITH monthly_revenue AS (
            SELECT 
                DATE_TRUNC('month', payment_date) AS month,
                SUM(amount) AS revenue
            FROM payments
            WHERE payment_status = 'Success'
            GROUP BY DATE_TRUNC('month', payment_date)
        ),
        revenue_with_stats AS (
            SELECT 
                month,
                revenue,
                LAG(revenue, 1) OVER (ORDER BY month) AS prev_month_revenue,
                AVG(revenue) OVER (
                    ORDER BY month 
                    ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
                ) AS avg_prev_6months
            FROM monthly_revenue
        )
        SELECT 
            month,
            revenue,
            prev_month_revenue,
            ROUND(
                ((revenue - prev_month_revenue)::DECIMAL / 
                 NULLIF(prev_month_revenue, 0)) * 100, 
                2
            ) AS mom_change_pct,
            CASE 
                WHEN ABS((revenue - prev_month_revenue)::DECIMAL / NULLIF(prev_month_revenue, 0)) > 0.15 
                THEN 'HIGH ANOMALY (>15% change)'
                WHEN ABS((revenue - prev_month_revenue)::DECIMAL / NULLIF(prev_month_revenue, 0)) > 0.10 
                THEN 'MEDIUM ANOMALY (>10% change)'
                ELSE 'Normal'
            END AS anomaly_flag
        FROM revenue_with_stats
        WHERE prev_month_revenue IS NOT NULL
        ORDER BY month DESC;
    """,
    
    'churn_spike_detection': """
        WITH monthly_churn AS (
            SELECT 
                DATE_TRUNC('month', end_date) AS month,
                COUNT(DISTINCT customer_id) AS churned_customers
            FROM subscriptions
            WHERE end_date IS NOT NULL
            GROUP BY DATE_TRUNC('month', end_date)
        ),
        churn_with_stats AS (
            SELECT 
                month,
                churned_customers,
                AVG(churned_customers) OVER (
                    ORDER BY month 
                    ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
                ) AS avg_prev_6months,
                STDDEV(churned_customers) OVER (
                    ORDER BY month 
                    ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
                ) AS stddev_prev_6months
            FROM monthly_churn
        )
        SELECT 
            month,
            churned_customers,
            ROUND(avg_prev_6months, 0) AS avg_prev_6months,
            CASE 
                WHEN churned_customers > (avg_prev_6months + 2 * COALESCE(stddev_prev_6months, 0))
                THEN 'CHURN SPIKE DETECTED'
                WHEN churned_customers > (avg_prev_6months + 1.5 * COALESCE(stddev_prev_6months, 0))
                THEN 'Elevated Churn'
                ELSE 'Normal'
            END AS anomaly_flag
        FROM churn_with_stats
        WHERE avg_prev_6months IS NOT NULL
        ORDER BY month DESC;
    """
}

def run_query(conn, query_name, query_sql):
    # run query
    try:
        df = pd.read_sql_query(query_sql, conn)
        print(f"  {query_name}: {len(df)} rows")
        return df
    except Exception as e:
        print(f"  {query_name} failed: {e}")
        return None

def save_results(all_results, output_dir='dashboard_data'):
    # save results
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # csv
    csv_dir = os.path.join(output_dir, 'csv')
    if not os.path.exists(csv_dir):
        os.makedirs(csv_dir)
    
    for name, df in all_results.items():
        if df is not None and not df.empty:
            csv_path = os.path.join(csv_dir, f"{name}.csv")
            df.to_csv(csv_path, index=False)
    
    # excel
    excel_path = os.path.join(output_dir, f'dashboard_data_{timestamp}.xlsx')
    try:
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            for name, df in all_results.items():
                if df is not None and not df.empty:
                    sheet_name = name[:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f"\n  Excel: {excel_path}")
    except ImportError:
        print("\n  Need openpyxl: pip install openpyxl")
    
    print(f"\n  CSV: {csv_dir}")

def main():
    print("Exporting dashboard data")
    
    try:
        print("\nConnecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("Connected\n")
        
        print(f"Running {len(QUERIES)} queries...\n")
        all_results = {}
        
        for query_name, query_sql in QUERIES.items():
            df = run_query(conn, query_name, query_sql)
            all_results[query_name] = df
        
        conn.close()
        
        print("\nSaving results...")
        save_results(all_results)
        
        print("\nDone!")
        print(f"\nFiles in 'dashboard_data' folder")
        print("Ready for Power BI / Tableau")
        
    except psycopg2.OperationalError as e:
        print(f"\nConnection failed: {e}")
        print("Check the configuration again")
        return 1
    except Exception as e:
        print(f"\nError: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
