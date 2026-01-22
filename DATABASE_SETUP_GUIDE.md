# Database Setup Guide - KPI Dashboard

This guide walks you through loading CSV data into PostgreSQL or MySQL.

## 📋 Prerequisites

### For PostgreSQL:
- PostgreSQL installed and running
- `psql` command-line tool (or pgAdmin)
- Python packages (optional): `pip install psycopg2-binary pandas`

### For MySQL:
- MySQL installed and running
- `mysql` command-line tool (or MySQL Workbench)
- Python packages (optional): `pip install mysql-connector-python pandas`

---

## 🐘 Method 1: PostgreSQL Setup

### Option A: Using SQL Script (Recommended)

1. **Create the database:**
```sql
CREATE DATABASE kpi_dashboard;
\c kpi_dashboard;
```

2. **Run the setup script:**
```bash
# From the project directory
psql -U postgres -d kpi_dashboard -f database_setup_postgresql.sql
```

**OR** manually in psql:
```bash
psql -U postgres -d kpi_dashboard
```
Then copy-paste the contents of `database_setup_postgresql.sql`.

**Note:** Update the file paths in the `\copy` commands to match your system:
```sql
\copy customers FROM 'C:/Users/prohi/OneDrive/Documents/Desktop/DataAnalysis_Projects/KPI_Dashboard/customers.csv' WITH (FORMAT csv, HEADER true, DELIMITER ',');
```

### Option B: Using Python Script

1. **Install dependencies:**
```bash
pip install psycopg2-binary pandas
```

2. **Edit `load_data_postgresql.py`:**
   - Update `DB_CONFIG` with your PostgreSQL credentials:
   ```python
   DB_CONFIG = {
       'host': 'localhost',
       'database': 'kpi_dashboard',
       'user': 'postgres',
       'password': 'your_password',
       'port': 5432
   }
   ```

3. **Run the script:**
```bash
python load_data_postgresql.py
```

---

## 🐬 Method 2: MySQL Setup

### Option A: Using SQL Script (Recommended)

1. **Create the database:**
```sql
CREATE DATABASE kpi_dashboard;
USE kpi_dashboard;
```

2. **Enable local file loading:**
```sql
SET GLOBAL local_infile = 1;
```

3. **Run the setup script:**
```bash
# From the project directory
mysql -u root -p kpi_dashboard < database_setup_mysql.sql
```

**OR** manually in mysql:
```bash
mysql -u root -p
USE kpi_dashboard;
```
Then copy-paste the contents of `database_setup_mysql.sql`.

**Note:** Update the file paths in the `LOAD DATA` commands:
```sql
LOAD DATA LOCAL INFILE 'C:/Users/prohi/OneDrive/Documents/Desktop/DataAnalysis_Projects/KPI_Dashboard/customers.csv'
INTO TABLE customers
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
```

### Option B: Using Python Script

1. **Install dependencies:**
```bash
pip install mysql-connector-python pandas
```

2. **Edit `load_data_mysql.py`:**
   - Update `DB_CONFIG` with your MySQL credentials:
   ```python
   DB_CONFIG = {
       'host': 'localhost',
       'database': 'kpi_dashboard',
       'user': 'root',
       'password': 'your_password',
       'port': 3306
   }
   ```

3. **Run the script:**
```bash
python load_data_mysql.py
```

---

## ✅ Verification

After loading data, verify the row counts:

### PostgreSQL:
```sql
SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM customers
UNION ALL
SELECT 'subscriptions', COUNT(*) FROM subscriptions
UNION ALL
SELECT 'payments', COUNT(*) FROM payments
UNION ALL
SELECT 'costs', COUNT(*) FROM costs;
```

### MySQL:
```sql
SELECT 'customers' AS table_name, COUNT(*) AS row_count FROM customers
UNION ALL
SELECT 'subscriptions', COUNT(*) FROM subscriptions
UNION ALL
SELECT 'payments', COUNT(*) FROM payments
UNION ALL
SELECT 'costs', COUNT(*) FROM costs;
```

**Expected Results:**
- customers: ~10,000 rows
- subscriptions: ~10,000 rows
- payments: ~166,000+ rows
- costs: 36 rows

---

## 🔧 Troubleshooting

### PostgreSQL Issues:

1. **"Permission denied" for COPY:**
   - Use `\copy` instead of `COPY` (client-side)
   - Or grant file permissions to PostgreSQL user

2. **"File not found":**
   - Use absolute paths in `\copy` commands
   - Ensure CSV files are in the correct location

### MySQL Issues:

1. **"local_infile is disabled":**
   ```sql
   SET GLOBAL local_infile = 1;
   ```
   Or add to `my.cnf`:
   ```
   [mysql]
   local_infile = 1
   ```

2. **"Access denied":**
   - Ensure MySQL user has FILE privilege
   - Check file path permissions

3. **"Empty end_date values":**
   - The SQL script handles NULL values correctly
   - If issues persist, use the Python script

---

## 📊 Quick Test Queries

After setup, test with these queries:

```sql
-- Check active vs churned subscriptions
SELECT 
    COUNT(*) AS total_subscriptions,
    SUM(CASE WHEN end_date IS NULL THEN 1 ELSE 0 END) AS active,
    SUM(CASE WHEN end_date IS NOT NULL THEN 1 ELSE 0 END) AS churned
FROM subscriptions;

-- Check revenue by month
SELECT 
    DATE_TRUNC('month', payment_date) AS month,
    SUM(amount) AS monthly_revenue
FROM payments
WHERE payment_status = 'Success'
GROUP BY month
ORDER BY month;

-- Check segment distribution
SELECT segment, COUNT(*) AS customer_count
FROM customers
GROUP BY segment
ORDER BY customer_count DESC;
```

---

## 🎯 Next Steps

Once data is loaded:
1. ✅ Verify row counts match expected values
2. ✅ Run test queries to ensure data integrity
3. ✅ Proceed to SQL query development for KPIs
4. ✅ Build dashboard visualizations

---

## 📝 Deliverable Checklist

- [ ] Database created
- [ ] Tables created with proper schema
- [ ] All CSV files imported
- [ ] Row counts verified
- [ ] Indexes created for performance
- [ ] Test queries executed successfully

**Status:** ✅ Raw data successfully ingested into relational database
