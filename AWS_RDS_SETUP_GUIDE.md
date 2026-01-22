# AWS RDS PostgreSQL Setup Guide

Complete guide for loading KPI Dashboard data into AWS RDS PostgreSQL.

## 📋 Prerequisites

1. **AWS RDS PostgreSQL instance running**
2. **Python 3.7+** installed locally
3. **Required packages:**
   ```bash
   pip install psycopg2-binary pandas
   ```

---

## 🔧 Step 1: Get Your AWS RDS Connection Details

### From AWS Console:

1. Go to **AWS Console > RDS > Databases**
2. Click on your PostgreSQL instance
3. Find these details in **"Connectivity & security"** section:

   - **Endpoint:** `your-db.abc123.us-east-1.rds.amazonaws.com`
   - **Port:** `5432` (default)
   - **Database name:** Usually `postgres` (or create `kpi_dashboard`)
   - **Master username:** Your admin username
   - **Master password:** Your admin password

### Example:
```
Endpoint: mydb-instance.abc123xyz.us-east-1.rds.amazonaws.com
Port: 5432
Database: postgres (or kpi_dashboard)
Username: postgres
Password: YourSecurePassword123!
```

---

## 🔒 Step 2: Configure Security Group

**Critical:** Your local IP must be allowed to connect.

1. Go to **RDS > Your Instance > Connectivity & security**
2. Click on **VPC security groups** link
3. Click **Edit inbound rules**
4. Add rule:
   - **Type:** PostgreSQL
   - **Port:** 5432
   - **Source:** Your IP address (or `0.0.0.0/0` for testing - **not recommended for production**)
5. Click **Save rules**

**To find your IP:** Google "what is my ip"

---

## ⚙️ Step 3: Configure the Python Script

1. **Open `load_data_postgresql.py`**

2. **Update the `DB_CONFIG` dictionary** (around line 15):

   ```python
   DB_CONFIG = {
       'host': 'your-db.abc123.us-east-1.rds.amazonaws.com',  # Your RDS endpoint
       'database': 'kpi_dashboard',  # Database name (will be created if doesn't exist)
       'user': 'postgres',  # Your master username
       'password': 'YourSecurePassword123!',  # Your master password
       'port': 5432,
       'sslmode': 'require'  # AWS RDS requires SSL
   }
   ```

3. **Save the file**

---

## 🚀 Step 4: Run the Script

1. **Ensure CSV files are in the same directory:**
   - `customers.csv`
   - `subscriptions.csv`
   - `payments.csv`
   - `costs.csv`

2. **Run the script:**
   ```bash
   python load_data_postgresql.py
   ```

3. **Expected output:**
   ```
   Connecting to AWS RDS (default database)...
   ✅ Database 'kpi_dashboard' already exists
   
   Connecting to AWS RDS PostgreSQL at your-db.abc123...
   ✅ Connected successfully
   
   ✅ Tables created successfully
   Loading customers...
      Loaded 10,000 customers
   Loading subscriptions...
      Loaded 10,000 subscriptions
   Loading payments...
      Loaded 166,726 payments
   Loading costs...
      Loaded 36 cost records
   
   ✅ All data loaded successfully
   
   📊 Data Verification:
   ----------------------------------------
      customers           10,000 rows
      subscriptions       10,000 rows
      payments           166,726 rows
      costs                  36 rows
   
      Active subscriptions: 7,500
      Churned subscriptions: 2,500
   
   ✅ Database setup complete!
   ```

---

## ✅ Step 5: Verify in AWS Console

1. Go to **AWS Console > RDS > Your Instance**
2. Click **Query Editor** (if available) or use a SQL client
3. Run verification query:

   ```sql
   SELECT 
       'customers' AS table_name, 
       COUNT(*) AS row_count 
   FROM customers
   UNION ALL
   SELECT 'subscriptions', COUNT(*) FROM subscriptions
   UNION ALL
   SELECT 'payments', COUNT(*) FROM payments
   UNION ALL
   SELECT 'costs', COUNT(*) FROM costs;
   ```

---

## 🔍 Troubleshooting

### Error: "could not connect to server"

**Causes:**
- Security group not allowing your IP
- Wrong endpoint address
- RDS instance not running

**Solutions:**
1. Check security group inbound rules (Step 2)
2. Verify endpoint in RDS console
3. Ensure RDS instance status is "Available"

---

### Error: "password authentication failed"

**Causes:**
- Wrong username or password
- Username case sensitivity

**Solutions:**
1. Double-check credentials in AWS RDS console
2. Try resetting master password if needed
3. Ensure username matches exactly (case-sensitive)

---

### Error: "SSL connection required"

**Causes:**
- AWS RDS requires SSL by default

**Solutions:**
- The script already includes `'sslmode': 'require'`
- If issues persist, try `'sslmode': 'prefer'`

---

### Error: "relation does not exist"

**Causes:**
- Tables not created
- Connected to wrong database

**Solutions:**
1. Re-run the script (it will drop and recreate tables)
2. Verify you're connected to the correct database

---

### Slow Connection / Timeout

**Causes:**
- Network latency
- Large data upload

**Solutions:**
1. Ensure you're in the same AWS region (if possible)
2. Use a VPN or EC2 instance in same VPC for faster upload
3. The script uses batch inserts for efficiency

---

## 🔗 Connecting from BI Tools

### Power BI:
1. **Get Data > Database > PostgreSQL database**
2. **Server:** Your RDS endpoint
3. **Database:** `kpi_dashboard`
4. **Username/Password:** Your RDS credentials
5. **SSL Mode:** Require

### Tableau:
1. **Connect > PostgreSQL**
2. **Server:** Your RDS endpoint
3. **Port:** 5432
4. **Database:** `kpi_dashboard`
5. **Authentication:** Username/Password
6. **Require SSL:** Yes

---

## 📊 Quick Test Queries

After setup, test with these:

```sql
-- Check row counts
SELECT 'customers' AS table_name, COUNT(*) AS rows FROM customers
UNION ALL SELECT 'subscriptions', COUNT(*) FROM subscriptions
UNION ALL SELECT 'payments', COUNT(*) FROM payments
UNION ALL SELECT 'costs', COUNT(*) FROM costs;

-- Check active vs churned
SELECT 
    COUNT(*) AS total,
    SUM(CASE WHEN end_date IS NULL THEN 1 ELSE 0 END) AS active,
    SUM(CASE WHEN end_date IS NOT NULL THEN 1 ELSE 0 END) AS churned
FROM subscriptions;

-- Monthly revenue
SELECT 
    DATE_TRUNC('month', payment_date) AS month,
    SUM(amount) AS revenue
FROM payments
WHERE payment_status = 'Success'
GROUP BY month
ORDER BY month;
```

---

## 🎯 Next Steps

Once data is loaded:
- ✅ [ ] Verify all row counts match expected values
- ✅ [ ] Test queries run successfully
- ✅ [ ] Connect Power BI / Tableau
- ✅ [ ] Proceed to SQL query development for KPIs

---

## 📝 Security Best Practices

1. **Never commit credentials to Git**
   - Use environment variables or config files (excluded from git)
   - Consider using AWS Secrets Manager for production

2. **Limit Security Group Access**
   - Only allow your IP, not `0.0.0.0/0`
   - Use VPN or bastion host for production

3. **Use IAM Database Authentication** (Advanced)
   - More secure than password authentication
   - Requires additional setup

---

## 💰 Cost Considerations

- **Data Transfer:** Uploading ~10MB of CSV data is free
- **Storage:** ~50MB database size (negligible cost)
- **No additional charges** for this setup

---

**Status:** ✅ Ready to load data into AWS RDS PostgreSQL
