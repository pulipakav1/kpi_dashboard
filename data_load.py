import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os

# db config
try:
    from config import DB_CONFIG
except ImportError:
    print("Error: config.py not found!")
    print("Copy config_template.py to config.py and add your database credentials")
    print("config.py is in .gitignore and won't be committed")
    exit(1)


def check_tables_exist(conn):
    # check tables
    cur = conn.cursor()
    tables = ['customers', 'subscriptions', 'payments', 'costs']
    existing_tables = {}
    
    for table in tables:
        try:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table,))
            exists = cur.fetchone()[0]
            existing_tables[table] = exists
            
            if exists:
                cur.execute(f"SELECT COUNT(*) FROM {table};")
                count = cur.fetchone()[0]
                existing_tables[f"{table}_count"] = count
        except Exception as e:
            existing_tables[table] = False
    
    return existing_tables

def drop_tables(conn):
    # drop tables
    cur = conn.cursor()
    
    print("Dropping tables...")
    cur.execute("DROP TABLE IF EXISTS payments CASCADE;")
    cur.execute("DROP TABLE IF EXISTS subscriptions CASCADE;")
    cur.execute("DROP TABLE IF EXISTS customers CASCADE;")
    cur.execute("DROP TABLE IF EXISTS costs CASCADE;")
    conn.commit()
    print("Done")

def create_tables(conn):
    cur = conn.cursor()
    
    # drop first
    print("Cleaning up...")
    cur.execute("DROP TABLE IF EXISTS payments CASCADE;")
    cur.execute("DROP TABLE IF EXISTS subscriptions CASCADE;")
    cur.execute("DROP TABLE IF EXISTS customers CASCADE;")
    cur.execute("DROP TABLE IF EXISTS costs CASCADE;")
    conn.commit()
    
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
    
    cur.execute("""
        CREATE TABLE costs (
            month VARCHAR(7) PRIMARY KEY,
            infra_cost DECIMAL(10, 2) NOT NULL,
            marketing_cost DECIMAL(10, 2) NOT NULL,
            support_cost DECIMAL(10, 2) NOT NULL
        );
    """)
    
    # add indexes
    cur.execute("CREATE INDEX idx_subscriptions_customer_id ON subscriptions(customer_id);")
    cur.execute("CREATE INDEX idx_subscriptions_start_date ON subscriptions(start_date);")
    cur.execute("CREATE INDEX idx_subscriptions_end_date ON subscriptions(end_date);")
    cur.execute("CREATE INDEX idx_payments_customer_id ON payments(customer_id);")
    cur.execute("CREATE INDEX idx_payments_payment_date ON payments(payment_date);")
    cur.execute("CREATE INDEX idx_customers_segment ON customers(segment);")
    cur.execute("CREATE INDEX idx_customers_signup_date ON customers(signup_date);")
    
    conn.commit()
    print("Tables created")

def load_data(conn):
    cur = conn.cursor()
    
    print("Loading customers...")
    df_customers = pd.read_csv('customers.csv')
    df_customers['signup_date'] = pd.to_datetime(df_customers['signup_date']).dt.date
    
    execute_values(
        cur,
        """INSERT INTO customers (customer_id, signup_date, segment, country, acquisition_channel, is_active)
           VALUES %s
           ON CONFLICT (customer_id) DO NOTHING""",
        [tuple(row) for row in df_customers.values]
    )
    print(f"   Loaded {len(df_customers):,} customers")
    
    print("Loading subscriptions...")
    df_subscriptions = pd.read_csv('subscriptions.csv')
    df_subscriptions['start_date'] = pd.to_datetime(df_subscriptions['start_date']).dt.date
    df_subscriptions['end_date'] = pd.to_datetime(df_subscriptions['end_date'], errors='coerce').dt.date
    df_subscriptions = df_subscriptions.where(pd.notnull(df_subscriptions), None)
    
    execute_values(
        cur,
        """INSERT INTO subscriptions (subscription_id, customer_id, plan_type, start_date, end_date, monthly_price)
           VALUES %s
           ON CONFLICT (subscription_id) DO NOTHING""",
        [tuple(row) for row in df_subscriptions.values]
    )
    print(f"   Loaded {len(df_subscriptions):,} subscriptions")
    
    print("Loading payments...")
    df_payments = pd.read_csv('payments.csv')
    df_payments['payment_date'] = pd.to_datetime(df_payments['payment_date']).dt.date
    
    execute_values(
        cur,
        """INSERT INTO payments (payment_id, customer_id, payment_date, amount, payment_status)
           VALUES %s
           ON CONFLICT (payment_id) DO NOTHING""",
        [tuple(row) for row in df_payments.values]
    )
    print(f"   Loaded {len(df_payments):,} payments")
    
    print("Loading costs...")
    df_costs = pd.read_csv('costs.csv')
    
    execute_values(
        cur,
        """INSERT INTO costs (month, infra_cost, marketing_cost, support_cost)
           VALUES %s
           ON CONFLICT (month) DO NOTHING""",
        [tuple(row) for row in df_costs.values]
    )
    print(f"   Loaded {len(df_costs)} cost records")
    
    conn.commit()
    print("\nAll data loaded successfully")

def verify_data(conn):
    # check counts
    cur = conn.cursor()
    
    tables = ['customers', 'subscriptions', 'payments', 'costs']
    print("\nVerification:")
    
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table};")
        count = cur.fetchone()[0]
        print(f"   {table:15} {count:>10,} rows")
    
    cur.execute("SELECT COUNT(*) FROM subscriptions WHERE end_date IS NULL;")
    active = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM subscriptions WHERE end_date IS NOT NULL;")
    churned = cur.fetchone()[0]
    print(f"\n   Active: {active:,}")
    print(f"   Churned: {churned:,}")

def main():
    try:
        print("Connecting to database...")
        print(f"   Host: {DB_CONFIG['host']}")
        print(f"   Database: {DB_CONFIG['database']}")
        conn = psycopg2.connect(**DB_CONFIG)
        print("Connected\n")
        
        existing_tables = check_tables_exist(conn)
        tables_exist = any(existing_tables.get(table) for table in ['customers', 'subscriptions', 'payments', 'costs'])
        
        if tables_exist:
            print("Tables already exist:")
            for table in ['customers', 'subscriptions', 'payments', 'costs']:
                if existing_tables.get(table):
                    count = existing_tables.get(f"{table}_count", 0)
                    print(f"   {table}: {count:,} rows")
            print("\nDropping to start fresh...")
        else:
            print("No existing tables")
        
        create_tables(conn)
        load_data(conn)
        verify_data(conn)
        
        conn.close()
        print("\nDone!")
        
    except psycopg2.OperationalError as e:
        print(f"\nConnection failed: {e}")
        print("Check the configuration again")
        return 1
        
    except psycopg2.errors.UniqueViolation as e:
        print(f"\nDuplicate key: {e}")
        print("Cleaning up and retrying...")
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            drop_tables(conn)
            create_tables(conn)
            load_data(conn)
            verify_data(conn)
            conn.close()
            print("\nDone after cleanup!")
        except Exception as e2:
            print(f"\nError: {e2}")
            return 1
        return 0
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    main()
