#!/usr/bin/env python3
"""
国际版 (mipham.ai) SaaS 数据库初始化脚本。
- 保留公司 1-3（空壳：只有科目结构，无业务数据）
- 用户注册从公司 4 开始
- 部署时运行一次: python3 init_saas_db.py
"""

import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from app.database import SessionLocal, init_db, run_migrations
from app.models import Company
from app.seed import seed_level1_accounts, seed_level2_accounts, seed_tax_accounts

DB_PATH = os.path.join(os.path.dirname(__file__), "saas-data", "finance.db")


def init():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    os.environ["DATABASE_URL"] = f"sqlite:///{DB_PATH}"

    # Create tables
    init_db()
    run_migrations()

    db = SessionLocal()

    # Reserve companies 1-3 (empty shells)
    reserved = [
        (1, "Rismed Ronxin Capital", "RRC"),
        (2, "One Mipham Corporation", "One Mipham"),
        (3, "MiphamAI Reserved", "MiphamAI"),
    ]
    for cid, name, short in reserved:
        existing = db.query(Company).filter(Company.id == cid).first()
        if not existing:
            db.add(
                Company(
                    id=cid,
                    name=name,
                    short_name=short,
                    internal_control_mode="standard",
                )
            )
            db.flush()
            seed_level1_accounts(db, cid)
            seed_level2_accounts(db, cid)
            seed_tax_accounts(db, cid)
            print(f"  ✅ Company {cid}: {name} — accounts seeded")

    db.commit()
    db.close()
    print(f"\n✅ SaaS DB ready: {DB_PATH}")
    print("   Companies 1-3 reserved. Public registration starts at company 4.")


if __name__ == "__main__":
    init()
