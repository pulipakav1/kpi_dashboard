"""
AWS RDS Configuration Template
Copy this file to 'config.py' and fill in your AWS RDS details.
DO NOT commit config.py to git (it's in .gitignore)
"""

# AWS RDS PostgreSQL Connection Configuration
DB_CONFIG = {
    # Your RDS endpoint (found in AWS Console > RDS > Your Instance > Connectivity)
    'host': 'your-db-instance.abc123.us-east-1.rds.amazonaws.com',
    
    # Database name (will be created if it doesn't exist)
    'database': 'kpi_dashboard',
    
    # Your RDS master username
    'user': 'postgres',
    
    # Your RDS master password
    'password': 'YourSecurePassword123!',
    
    # Port (usually 5432 for PostgreSQL)
    'port': 5432,
    
    # AWS RDS requires SSL
    'sslmode': 'require'
}

# Example:
# DB_CONFIG = {
#     'host': 'mydb-instance.abc123xyz.us-east-1.rds.amazonaws.com',
#     'database': 'kpi_dashboard',
#     'user': 'postgres',
#     'password': 'MySecurePass123!',
#     'port': 5432,
#     'sslmode': 'require'
# }
