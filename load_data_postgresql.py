"""
PostgreSQL Data Loader Script
Alternative method using Python + psycopg2
"""
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'database': 'kpi_dashboard',
    'user': 'postgres',
    'password': 'your_password',  # Change this
    'port': 5432
}

def create_tables(conn):
    """Create all tables"""
    cur = conn.cursor()
    
    # Drop tables if they exist (for clean setup)
    cur.execute("DROP TABLE IF EXISTS payments CASCADE;")
    cur.execute("DROP TABLE IF EXISTS subscriptions CASCADE;")
    cur.execute("DROP TABLE IF EXISTS customers CASCADE;")
    cur.execute("DROP TABLE IF EXISTS costs CASCADE;")
    
    # Create customers table
    cur.execute("""
        CREATE TABLE customers (
            customer_id VARCHAR(20) PRIMARY KEY,
            signup_date DATE NOT NULL,
            segment VARCHAR(20) NOT NULL,
            country VARCHAR(5) NOT NULL,
            acquisition_channel VARCHAR(50) NOT NULL,
            is_active BOOLEAN NOT NULL
        );
    """)
    
    # Create subscriptions table
    cur.execute("""
        CREATE TABLE subscriptions (
            subscription_id VARCHAR(20) PRIMARY KEY,
            customer_id VARCHAR(20) NOT NULL,
            plan_type VARCHAR(20) NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE,
            monthly_price DECIMAL(10, 2) NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        );
    """)
    
    # Create payments table
    cur.execute("""
        CREATE TABLE payments (
            payment_id VARCHAR(20) PRIMARY KEY,
            customer_id VARCHAR(20) NOT NULL,
            payment_date DATE NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            payment_status VARCHAR(20) NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        );
    """)
    
    # Create costs table
    cur.execute("""
        CREATE TABLE costs (
            month VARCHAR(7) PRIMARY KEY,
            infra_cost DECIMAL(10, 2) NOT NULL,
            marketing_cost DECIMAL(10, 2) NOT NULL,
            support_cost DECIMAL(10, 2) NOT NULL
        );
    """)
    
    # Create indexes
    cur.execute("CREATE INDEX idx_subscriptions_customer_id ON subscriptions(customer_id);")
    cur.execute("CREATE INDEX idx_subscriptions_start_date ON subscriptions(start_date);")
    cur.execute("CREATE INDEX idx_subscriptions_end_date ON subscriptions(end_date);")
    cur.execute("CREATE INDEX idx_payments_customer_id ON payments(customer_id);")
    cur.execute("CREATE INDEX idx_payments_payment_date ON payments(payment_date);")
    cur.execute("CREATE INDEX idx_customers_segment ON customers(segment);")
    cur.execute("CREATE INDEX idx_customers_signup_date ON customers(signup_date);")
    
    conn.commit()
    print("✅ Tables created successfully")

def load_data(conn):
    """Load CSV data into tables"""
    cur = conn.cursor()
    
    # Load customers
    print("Loading customers...")
    df_customers = pd.read_csv('customers.csv')
    df_customers['signup_date'] = pd.to_datetime(df_customers['signup_date']).dt.date
    execute_values(
        cur,
        """INSERT INTO customers (customer_id, signup_date, segment, country, acquisition_channel, is_active)
           VALUES %s""",
        [tuple(row) for row in df_customers.values]
    )
    print(f"   Loaded {len(df_customers):,} customers")
    
    # Load subscriptions
    print("Loading subscriptions...")
    df_subscriptions = pd.read_csv('subscriptions.csv')
    df_subscriptions['start_date'] = pd.to_datetime(df_subscriptions['start_date']).dt.date
    df_subscriptions['end_date'] = pd.to_datetime(df_subscriptions['end_date'], errors='coerce').dt.date
    df_subscriptions = df_subscriptions.where(pd.notnull(df_subscriptions), None)
    execute_values(
        cur,
        """INSERT INTO subscriptions (subscription_id, customer_id, plan_type, start_date, end_date, monthly_price)
           VALUES %s""",
        [tuple(row) for row in df_subscriptions.values]
    )
    print(f"   Loaded {len(df_subscriptions):,} subscriptions")
    
    # Load payments
    print("Loading payments...")
    df_payments = pd.read_csv('payments.csv')
    df_payments['payment_date'] = pd.to_datetime(df_payments['payment_date']).dt.date
    execute_values(
        cur,
        """INSERT INTO payments (payment_id, customer_id, payment_date, amount, payment_status)
           VALUES %s""",
        [tuple(row) for row in df_payments.values]
    )
    print(f"   Loaded {len(df_payments):,} payments")
    
    # Load costs
    print("Loading costs...")
    df_costs = pd.read_csv('costs.csv')
    execute_values(
        cur,
        """INSERT INTO costs (month, infra_cost, marketing_cost, support_cost)
           VALUES %s""",
        [tuple(row) for row in df_costs.values]
    )
    print(f"   Loaded {len(df_costs)} cost records")
    
    conn.commit()
    print("\n✅ All data loaded successfully")

def verify_data(conn):
    """Verify row counts"""
    cur = conn.cursor()
    
    tables = ['customers', 'subscriptions', 'payments', 'costs']
    print("\n📊 Data Verification:")
    print("-" * 40)
    
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table};")
        count = cur.fetchone()[0]
        print(f"   {table:15} {count:>10,} rows")
    
    # Additional checks
    cur.execute("SELECT COUNT(*) FROM subscriptions WHERE end_date IS NULL;")
    active = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM subscriptions WHERE end_date IS NOT NULL;")
    churned = cur.fetchone()[0]
    print(f"\n   Active subscriptions: {active:,}")
    print(f"   Churned subscriptions: {churned:,}")

def main():
    """Main execution"""
    try:
        # Connect to database
        print("Connecting to PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Connected successfully\n")
        
        # Create tables
        create_tables(conn)
        
        # Load data
        load_data(conn)
        
        # Verify
        verify_data(conn)
        
        conn.close()
        print("\n✅ Database setup complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    main()
