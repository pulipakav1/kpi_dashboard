-- ============================================
-- PostgreSQL Database Setup for KPI Dashboard
-- ============================================

-- Create database (run this separately if needed)
-- CREATE DATABASE kpi_dashboard;
-- \c kpi_dashboard;

-- ============================================
-- 1. CREATE TABLES
-- ============================================

-- Customers table
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    signup_date DATE NOT NULL,
    segment VARCHAR(20) NOT NULL,
    country VARCHAR(5) NOT NULL,
    acquisition_channel VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL
);

-- Subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    plan_type VARCHAR(20) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    monthly_price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Payments table
CREATE TABLE IF NOT EXISTS payments (
    payment_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    payment_date DATE NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_status VARCHAR(20) NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

-- Costs table
CREATE TABLE IF NOT EXISTS costs (
    month VARCHAR(7) PRIMARY KEY,
    infra_cost DECIMAL(10, 2) NOT NULL,
    marketing_cost DECIMAL(10, 2) NOT NULL,
    support_cost DECIMAL(10, 2) NOT NULL
);

-- ============================================
-- 2. CREATE INDEXES FOR PERFORMANCE
-- ============================================

CREATE INDEX IF NOT EXISTS idx_subscriptions_customer_id ON subscriptions(customer_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_start_date ON subscriptions(start_date);
CREATE INDEX IF NOT EXISTS idx_subscriptions_end_date ON subscriptions(end_date);
CREATE INDEX IF NOT EXISTS idx_payments_customer_id ON payments(customer_id);
CREATE INDEX IF NOT EXISTS idx_payments_payment_date ON payments(payment_date);
CREATE INDEX IF NOT EXISTS idx_customers_segment ON customers(segment);
CREATE INDEX IF NOT EXISTS idx_customers_signup_date ON customers(signup_date);

-- ============================================
-- 3. IMPORT CSV FILES
-- ============================================
-- Note: Adjust the file paths to match your system
-- On Windows, use forward slashes or double backslashes

-- Import customers
\copy customers FROM 'customers.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

-- Import subscriptions
\copy subscriptions FROM 'subscriptions.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

-- Import payments
\copy payments FROM 'payments.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

-- Import costs
\copy costs FROM 'costs.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');

-- ============================================
-- 4. VERIFY DATA LOADED
-- ============================================

SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM customers
UNION ALL
SELECT 'subscriptions', COUNT(*) FROM subscriptions
UNION ALL
SELECT 'payments', COUNT(*) FROM payments
UNION ALL
SELECT 'costs', COUNT(*) FROM costs;

-- Sample data verification
SELECT 'Sample customers' AS check_type, COUNT(*) AS count FROM customers;
SELECT 'Sample subscriptions (active)', COUNT(*) FROM subscriptions WHERE end_date IS NULL;
SELECT 'Sample subscriptions (churned)', COUNT(*) FROM subscriptions WHERE end_date IS NOT NULL;
SELECT 'Sample payments (success)', COUNT(*) FROM payments WHERE payment_status = 'Success';
SELECT 'Sample payments (failed)', COUNT(*) FROM payments WHERE payment_status = 'Failed';
