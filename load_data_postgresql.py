"""
PostgreSQL Data Loader Script for AWS RDS
Uses Python + psycopg2 to load CSV data into AWS RDS PostgreSQL
"""
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os

# ============================================
# AWS RDS PostgreSQL Connection Configuration
# ============================================
# Option 1: Use config.py file (recommended - keeps credentials separate)
#   - Copy config_template.py to config.py
#   - Fill in your AWS RDS details
#   - config.py is in .gitignore (won't be committed)
#
# Option 2: Update DB_CONFIG directly below

try:
    # Try to import from config.py if it exists
    from config import DB_CONFIG
    print("✅ Using configuration from config.py")
except ImportError:
    # Fall back to inline configuration
    print("⚠️  config.py not found, using inline configuration")
    print("   💡 Tip: Copy config_template.py to config.py for better security")
    
    DB_CONFIG = {
        'host': 'your-rds-endpoint.region.rds.amazonaws.com',  # e.g., 'mydb.abc123.us-east-1.rds.amazonaws.com'
        'database': 'kpi_dashboard',  # Create this database first if needed
        'user': 'postgres',  # Your RDS master username
        'password': 'your_password',  # Your RDS master password
        'port': 5432,
        'sslmode': 'require'  # AWS RDS requires SSL
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

def create_database_if_not_exists():
    """Create database if it doesn't exist (connect to default 'postgres' DB first)"""
    try:
        # Connect to default postgres database to create our database
        temp_config = DB_CONFIG.copy()
        temp_config['database'] = 'postgres'  # Connect to default database
        
        print("Connecting to AWS RDS (default database)...")
        conn = psycopg2.connect(**temp_config)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_CONFIG['database'],))
        exists = cur.fetchone()
        
        if not exists:
            print(f"Creating database '{DB_CONFIG['database']}'...")
            cur.execute(f"CREATE DATABASE {DB_CONFIG['database']};")
            print("✅ Database created")
        else:
            print(f"✅ Database '{DB_CONFIG['database']}' already exists")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"⚠️  Could not create database (may already exist): {e}")
        print("   Continuing with existing database...")

def main():
    """Main execution"""
    try:
        # Create database if needed
        create_database_if_not_exists()
        
        # Connect to database
        print(f"\nConnecting to AWS RDS PostgreSQL at {DB_CONFIG['host']}...")
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
        print("\n📝 Next Steps:")
        print("   1. Verify data in AWS RDS Console")
        print("   2. Proceed to SQL query development for KPIs")
        print("   3. Connect Power BI / Tableau to this database")
        
    except psycopg2.OperationalError as e:
        print(f"\n❌ Connection Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check your AWS RDS endpoint is correct")
        print("   2. Verify security group allows your IP (port 5432)")
        print("   3. Confirm username and password are correct")
        print("   4. Ensure RDS instance is running")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    main()
