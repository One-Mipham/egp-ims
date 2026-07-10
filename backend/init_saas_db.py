#!/usr/bin/env python3
"""Initialize the SaaS (mipham.ai) database with English defaults and company ID starting from 1004."""

import os, sys

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, init_db
from app.seed import seed_subscription_plans

# 1. Create all tables
init_db()
print("Tables created.")

db = SessionLocal()

# 2. Seed subscription plans
seed_subscription_plans(db)
print("Subscription plans seeded.")

# 3. Set company auto-increment to start from 1004 (SQLite only)
import sqlite3  # noqa: E402

db_url = os.environ.get("DATABASE_URL", "sqlite:///./finance.db")
db_path = db_url.replace("sqlite:///", "")
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Check current max company ID
c.execute("SELECT COALESCE(MAX(id), 0) FROM companies")
current_max = c.fetchone()[0]
target_seq = 1003  # next INSERT will get 1004

if current_max >= target_seq:
    print(f"Company IDs already at {current_max}, sequence not modified.")
else:
    c.execute("UPDATE sqlite_sequence SET seq = ? WHERE name = 'companies'", (target_seq,))
    conn.commit()
    print(f"Company auto-increment set to start from {target_seq + 1} (was {current_max})")

conn.close()
db.close()
print("SaaS database initialized successfully.")
