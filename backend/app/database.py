"""数据库统一接口，通过 SQLAlchemy 抽象层，未来换 PostgreSQL 只需改连接字符串。"""

import contextlib
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./finance.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """创建所有表。"""
    Base.metadata.create_all(bind=engine)


def run_migrations():
    """对已有表追加新列（SQLite 兼容）。"""
    import sqlite3

    db_url = DATABASE_URL.replace("sqlite:///", "")
    conn = sqlite3.connect(db_url)
    c = conn.cursor()
    migrations = [
        "ALTER TABLE accounts ADD COLUMN aux_dept INTEGER DEFAULT 0",
        "ALTER TABLE accounts ADD COLUMN aux_person INTEGER DEFAULT 0",
        "ALTER TABLE accounts ADD COLUMN aux_counterparty INTEGER DEFAULT 0",
        "ALTER TABLE voucher_entries ADD COLUMN counterparty_id INTEGER REFERENCES counterparties(id)",
        "ALTER TABLE voucher_entries ADD COLUMN person_id INTEGER REFERENCES persons(id)",
        "ALTER TABLE fixed_assets ADD COLUMN disposal_date VARCHAR(10)",
        "ALTER TABLE fixed_assets ADD COLUMN disposal_proceeds FLOAT DEFAULT 0",
        "ALTER TABLE fixed_assets ADD COLUMN disposal_gain_loss FLOAT DEFAULT 0",
        "ALTER TABLE fixed_assets ADD COLUMN disposal_reason TEXT",
        "ALTER TABLE fixed_asset_depreciations ADD COLUMN updated_at TIMESTAMP",
        "CREATE TABLE IF NOT EXISTS kb_categories (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER NOT NULL REFERENCES companies(id), name VARCHAR(100) NOT NULL, parent_id INTEGER REFERENCES kb_categories(id), level INTEGER NOT NULL DEFAULT 1, sort_order INTEGER NOT NULL DEFAULT 0, is_system BOOLEAN NOT NULL DEFAULT 0, is_active BOOLEAN NOT NULL DEFAULT 1, created_by INTEGER REFERENCES users(id), created_at TIMESTAMP, updated_at TIMESTAMP)",  # noqa: E501
        "ALTER TABLE kb_articles ADD COLUMN category_id INTEGER REFERENCES kb_categories(id)",
        "CREATE TABLE IF NOT EXISTS bank_settlements (id INTEGER PRIMARY KEY AUTOINCREMENT, voucher_entry_id INTEGER NOT NULL REFERENCES voucher_entries(id), seq INTEGER NOT NULL, settlement_method VARCHAR(20) NOT NULL, account_name VARCHAR(100), instrument_no VARCHAR(50), instrument_date VARCHAR(10), direction VARCHAR(6) NOT NULL DEFAULT 'debit', amount FLOAT DEFAULT 0)",  # noqa: E501
        "ALTER TABLE users ADD COLUMN company_id INTEGER REFERENCES companies(id)",
        "CREATE TABLE IF NOT EXISTS voucher_sequences (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER NOT NULL REFERENCES companies(id), voucher_type VARCHAR(10) NOT NULL, period VARCHAR(7) NOT NULL, last_seq INTEGER NOT NULL DEFAULT 0, UNIQUE(company_id, voucher_type, period))",  # noqa: E501
        # 2026-07-08: 部门层级 + 用户公司归属 + 预算/现金流增强
        "ALTER TABLE departments ADD COLUMN parent_id INTEGER REFERENCES departments(id)",
        "ALTER TABLE departments ADD COLUMN updated_at TIMESTAMP",
        "ALTER TABLE budgets ADD COLUMN revenue_growth_rate FLOAT",
        "ALTER TABLE budgets ADD COLUMN manual_adjustment FLOAT",
        "ALTER TABLE budgets ADD COLUMN cost_rate FLOAT",
        "ALTER TABLE budgets ADD COLUMN operating_exp_rate FLOAT",
        "ALTER TABLE budgets ADD COLUMN admin_exp_rate FLOAT",
        "ALTER TABLE budgets ADD COLUMN finance_exp_rate FLOAT",
        "CREATE TABLE IF NOT EXISTS cashflow_plans (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER NOT NULL REFERENCES companies(id), name VARCHAR(100) NOT NULL, year INTEGER NOT NULL, status VARCHAR(10) DEFAULT 'draft', created_by INTEGER REFERENCES users(id), created_at TIMESTAMP)",  # noqa: E501
        "CREATE TABLE IF NOT EXISTS cashflow_plan_items (id INTEGER PRIMARY KEY AUTOINCREMENT, plan_id INTEGER NOT NULL REFERENCES cashflow_plans(id), account_code VARCHAR(10) NOT NULL, month VARCHAR(7) NOT NULL, amount FLOAT DEFAULT 0)",  # noqa: E501
        # 将无公司归属的用户关联到公司 1（青岛利美融信）
        "UPDATE users SET company_id = 1 WHERE company_id IS NULL",
    ]
    for sql in migrations:
        with contextlib.suppress(Exception):  # 列已存在则跳过
            c.execute(sql)
    conn.commit()
    conn.close()
