# Fix: Connection Timeout to AWS RDS

## 🔒 Problem
```
Connection timed out (0x0000274C/10060)
Is the server running on that host and accepting TCP/IP connections?
```

This means your **security group is blocking your IP address**.

---

## ✅ Solution: Update Security Group (5 minutes)

### Step-by-Step Instructions:

1. **Open AWS Console**
   - Go to https://console.aws.amazon.com
   - Navigate to **RDS** service

2. **Find Your Database**
   - Click **Databases** in left sidebar
   - Click on **database-1** (your instance)

3. **Go to Security Settings**
   - Click the **"Connectivity & security"** tab
   - Scroll down to **"Security"** section
   - You'll see **"VPC security groups"** with a link like `sg-xxxxx`
   - **Click on that security group link**

4. **Edit Inbound Rules**
   - You'll be taken to **EC2 > Security Groups**
   - Click the **"Inbound rules"** tab
   - Click **"Edit inbound rules"** button

5. **Add PostgreSQL Rule**
   - Click **"Add rule"** button
   - Configure:
     - **Type:** Select `PostgreSQL` (or `Custom TCP`)
     - **Port range:** `5432`
     - **Source:** 
       - Option 1: Click dropdown → Select **"My IP"** (AWS detects your IP)
       - Option 2: Manually enter your IP (find it at https://whatismyip.com)
     - **Description:** "Allow PostgreSQL from my computer"

6. **Save**
   - Click **"Save rules"** button

7. **Wait 10-30 seconds** for changes to propagate

8. **Try Again**
   ```bash
   python load_data_postgresql.py
   ```

---

## 🖼️ Visual Guide

### Step 3-4: Finding Security Group
```
RDS Console > database-1 > Connectivity & security tab
  ↓
Security section
  ↓
VPC security groups: sg-abc123xyz (click this link)
  ↓
EC2 Security Groups page opens
```

### Step 5: Adding Rule
```
Inbound rules tab > Edit inbound rules > Add rule

Type:        PostgreSQL
Port:        5432
Source:      My IP (or your IP address)
Description: Allow PostgreSQL from my computer
```

---

## 🔍 Alternative: Check Current Rules

If you want to see what's currently allowed:

1. Go to **EC2 > Security Groups**
2. Find your RDS security group
3. Check **Inbound rules** tab
4. Look for rules allowing port 5432

**Common Issues:**
- ❌ No rule for port 5432
- ❌ Rule exists but source is wrong IP
- ❌ Rule exists but only allows specific IPs (not yours)

---

## 🌐 Finding Your IP Address

**Method 1: AWS Auto-Detect**
- In the security group rule, select **"My IP"** from dropdown
- AWS automatically detects your current IP

**Method 2: Manual Lookup**
- Visit: https://whatismyip.com
- Copy your IPv4 address
- Paste it in the Source field (format: `x.x.x.x/32`)

**Method 3: Command Line**
```bash
# Windows PowerShell
(Invoke-WebRequest -Uri "https://api.ipify.org").Content

# Or visit in browser
https://api.ipify.org
```

---

## ⚠️ Important Notes

### Dynamic IP Addresses
- If your IP changes frequently (home internet), you'll need to update the rule
- Consider using a **VPN with static IP** for production
- Or temporarily allow `0.0.0.0/0` for testing (⚠️ **NOT SECURE** - only for testing!)

### Multiple Locations
- If you work from multiple locations, add rules for each IP
- Or use a VPN to have a consistent IP

### Corporate Networks
- If behind a corporate firewall, you may need to whitelist AWS RDS IPs
- Contact your IT department

---

## 🧪 Test Connection

After updating security group, test with:

```bash
python load_data_postgresql.py
```

**Success looks like:**
```
Connecting to AWS RDS PostgreSQL...
   Host: database-1.cbumigc8isn9.us-east-2.rds.amazonaws.com
   Database: database-1
✅ Connected successfully
```

---

## 🔐 Security Best Practices

1. **Never use `0.0.0.0/0`** in production (allows anyone)
2. **Use specific IP addresses** when possible
3. **Remove old IPs** when you no longer need them
4. **Use VPN** for consistent IP addresses
5. **Review security groups regularly**

---

## 📞 Still Not Working?

If connection still fails after updating security group:

1. **Verify RDS is running:**
   - Status should be **"Available"** (not "Stopped" or "Modifying")

2. **Check endpoint:**
   - Make sure endpoint in script matches RDS console

3. **Verify credentials:**
   - Username and password are correct
   - Try connecting with a SQL client (pgAdmin, DBeaver) to test

4. **Check VPC/Network:**
   - RDS might be in private subnet (requires VPN/bastion)
   - Check if RDS has public accessibility enabled

5. **Wait longer:**
   - Security group changes can take 1-2 minutes to propagate

---

## ✅ Quick Checklist

- [ ] Security group inbound rule added for port 5432
- [ ] Source IP is your current IP address
- [ ] Rule saved successfully
- [ ] Waited 30 seconds after saving
- [ ] RDS instance status is "Available"
- [ ] Tried running script again

---

**After fixing, your script should connect successfully!** 🎉
