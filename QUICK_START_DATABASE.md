# Quick Start: Load Data into Database

## 🚀 Fastest Method (Choose One)

### PostgreSQL (Recommended)

**Step 1:** Open PowerShell/Command Prompt in project directory

**Step 2:** Connect to PostgreSQL and create database
```bash
psql -U postgres
```
```sql
CREATE DATABASE kpi_dashboard;
\c kpi_dashboard;
```

**Step 3:** Run setup script (update file paths first!)
```bash
# Edit database_setup_postgresql.sql to update CSV file paths
# Then run:
psql -U postgres -d kpi_dashboard -f database_setup_postgresql.sql
```

**OR use Python (easier):**
```bash
pip install psycopg2-binary pandas
# Edit load_data_postgresql.py with your DB credentials
python load_data_postgresql.py
```

---

### MySQL

**Step 1:** Open PowerShell/Command Prompt in project directory

**Step 2:** Connect to MySQL and create database
```bash
mysql -u root -p
```
```sql
CREATE DATABASE kpi_dashboard;
USE kpi_dashboard;
SET GLOBAL local_infile = 1;
```

**Step 3:** Run setup script (update file paths first!)
```bash
# Edit database_setup_mysql.sql to update CSV file paths
# Then run:
mysql -u root -p kpi_dashboard < database_setup_mysql.sql
```

**OR use Python (easier):**
```bash
pip install mysql-connector-python pandas
# Edit load_data_mysql.py with your DB credentials
python load_data_mysql.py
```

---

## ✅ Verify It Worked

Run this in your database:
```sql
SELECT 'customers' AS table, COUNT(*) AS rows FROM customers
UNION ALL SELECT 'subscriptions', COUNT(*) FROM subscriptions
UNION ALL SELECT 'payments', COUNT(*) FROM payments
UNION ALL SELECT 'costs', COUNT(*) FROM costs;
```

Expected: ~10K customers, ~10K subscriptions, ~166K payments, 36 costs

---

## 📁 Files Created

- `database_setup_postgresql.sql` - PostgreSQL SQL script
- `database_setup_mysql.sql` - MySQL SQL script  
- `load_data_postgresql.py` - Python loader for PostgreSQL
- `load_data_mysql.py` - Python loader for MySQL
- `DATABASE_SETUP_GUIDE.md` - Detailed guide

**See `DATABASE_SETUP_GUIDE.md` for detailed instructions and troubleshooting.**
