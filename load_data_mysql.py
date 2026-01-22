"""
MySQL Data Loader Script
Alternative method using Python + mysql-connector-python
"""
import pandas as pd
import mysql.connector
from mysql.connector import Error
import os

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'database': 'kpi_dashboard',
    'user': 'root',
    'password': 'your_password',  # Change this
    'port': 3306
}

def create_tables(conn):
    """Create all tables"""
    cur = conn.cursor()
    
    # Drop tables if they exist (for clean setup)
    cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
    cur.execute("DROP TABLE IF EXISTS payments;")
    cur.execute("DROP TABLE IF EXISTS subscriptions;")
    cur.execute("DROP TABLE IF EXISTS customers;")
    cur.execute("DROP TABLE IF EXISTS costs;")
    cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
    
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
            end_date DATE NULL,
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
    
    insert_query = """INSERT INTO customers 
                      (customer_id, signup_date, segment, country, acquisition_channel, is_active)
                      VALUES (%s, %s, %s, %s, %s, %s)"""
    cur.executemany(insert_query, [tuple(row) for row in df_customers.values])
    print(f"   Loaded {len(df_customers):,} customers")
    
    # Load subscriptions
    print("Loading subscriptions...")
    df_subscriptions = pd.read_csv('subscriptions.csv')
    df_subscriptions['start_date'] = pd.to_datetime(df_subscriptions['start_date']).dt.date
    df_subscriptions['end_date'] = pd.to_datetime(df_subscriptions['end_date'], errors='coerce').dt.date
    df_subscriptions = df_subscriptions.where(pd.notnull(df_subscriptions), None)
    
    insert_query = """INSERT INTO subscriptions 
                      (subscription_id, customer_id, plan_type, start_date, end_date, monthly_price)
                      VALUES (%s, %s, %s, %s, %s, %s)"""
    cur.executemany(insert_query, [tuple(row) for row in df_subscriptions.values])
    print(f"   Loaded {len(df_subscriptions):,} subscriptions")
    
    # Load payments
    print("Loading payments...")
    df_payments = pd.read_csv('payments.csv')
    df_payments['payment_date'] = pd.to_datetime(df_payments['payment_date']).dt.date
    
    insert_query = """INSERT INTO payments 
                      (payment_id, customer_id, payment_date, amount, payment_status)
                      VALUES (%s, %s, %s, %s, %s)"""
    cur.executemany(insert_query, [tuple(row) for row in df_payments.values])
    print(f"   Loaded {len(df_payments):,} payments")
    
    # Load costs
    print("Loading costs...")
    df_costs = pd.read_csv('costs.csv')
    
    insert_query = """INSERT INTO costs 
                      (month, infra_cost, marketing_cost, support_cost)
                      VALUES (%s, %s, %s, %s)"""
    cur.executemany(insert_query, [tuple(row) for row in df_costs.values])
    print(f"   Loaded {len(df_costs)} cost records")
    
    conn.commit()
    print("\n✅ All data loaded successfully")

def verify_data(conn):
    """Verify row counts"""
    cur = conn.cursor()
    
    tables = ['customers', 'subscriptions', 'payments', 'costs']
    print("\n📊 Data Verification:")
    
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
        print("Connecting to MySQL...")
        conn = mysql.connector.connect(**DB_CONFIG)
        print("✅ Connected successfully\n")
        
        # Create tables
        create_tables(conn)
        
        # Load data
        load_data(conn)
        
        # Verify
        verify_data(conn)
        
        conn.close()
        print("\n✅ Database setup complete!")
        
    except Error as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    main()
