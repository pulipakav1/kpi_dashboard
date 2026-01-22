# Quick Start: AWS RDS PostgreSQL Setup

## 🚀 3-Step Setup

### Step 1: Get Your RDS Endpoint
- AWS Console > RDS > Your Instance > **Connectivity & security**
- Copy the **Endpoint** (e.g., `mydb.abc123.us-east-1.rds.amazonaws.com`)

### Step 2: Configure Security Group
- RDS > Your Instance > **VPC security groups** > Edit inbound rules
- Add: **PostgreSQL, Port 5432, Source: Your IP**

### Step 3: Run the Script

**Option A: Use config file (Recommended)**
```bash
# 1. Copy template
copy config_template.py config.py

# 2. Edit config.py with your RDS details
# 3. Run script
python load_data_postgresql.py
```

**Option B: Edit script directly**
```bash
# 1. Edit load_data_postgresql.py
# 2. Update DB_CONFIG with your RDS details
# 3. Run script
python load_data_postgresql.py
```

---

## ⚙️ Configuration Template

```python
DB_CONFIG = {
    'host': 'your-db.abc123.us-east-1.rds.amazonaws.com',  # Your endpoint
    'database': 'kpi_dashboard',
    'user': 'postgres',  # Your master username
    'password': 'YourPassword123!',  # Your master password
    'port': 5432,
    'sslmode': 'require'
}
```

---

## ✅ Verify It Worked

The script will show:
```
✅ Connected successfully
✅ Tables created successfully
   Loaded 10,000 customers
   Loaded 10,000 subscriptions
   Loaded 166,726 payments
   Loaded 36 cost records
```

---

## 🔧 Troubleshooting

**"could not connect"** → Check security group allows your IP

**"password authentication failed"** → Verify username/password in AWS Console

**"SSL required"** → Already handled (sslmode: require)

---

## 📚 Full Guide

See `AWS_RDS_SETUP_GUIDE.md` for detailed instructions.
