"""
预置三家公司内部用户 — 利美融信资本内部系统专用。

三家预置公司（ID 1-3），不对外开放注册。
每个公司一个预置管理员用户，统一密码 Rismed2026!。

用法:
    cd backend
    uv run python seed_internal_users.py
"""
import os
import sys
import sqlite3
import bcrypt

DB_PATH = os.environ.get("DATABASE_URL", "sqlite:///./finance.db").replace("sqlite:///", "")

# ═══════════ 预置公司数据 ═══════════
COMPANIES = [
    {
        "id": 1,
        "name": "青岛利美融信投资控股有限责任公司",
        "short_name": "利美融信资本",
        "english_name": "Rismed Ronxin Capital Investment Holding Co., Ltd.",
        "english_short_name": "Rismed Ronxin Capital",
        "industry": "investment",
        "internal_control_mode": "strict",
        "currency": "CNY",
        "tax_region": "青岛市",
        "email": "contact@rismedronxin.com",
        "website": "https://www.rismedronxin.com",
    },
    {
        "id": 2,
        "name": "北京华安麦逄科技有限公司",
        "short_name": "华安麦逄科技",
        "english_name": "One Mipham Corporation (Beijing)",
        "english_short_name": "One Mipham (Beijing)",
        "industry": "tech_dev",
        "internal_control_mode": "strict",
        "currency": "CNY",
        "tax_region": "北京市",
        "email": "contact@onemipham.com",
        "website": "https://www.onemipham.com",
    },
    {
        "id": 3,
        "name": "One Mipham Corporation",
        "short_name": "One Mipham",
        "english_name": "One Mipham Corporation",
        "english_short_name": "One Mipham (Delaware)",
        "industry": "ai",
        "internal_control_mode": "strict",
        "currency": "USD",
        "tax_region": "Delaware, USA",
        "email": "contact@mipham.ai",
        "website": "https://www.mipham.ai",
    },
]

# ═══════════ 预置用户数据 ═══════════
# 用户名 = 邮箱，密码 = Rismed2026! (用 bcrypt 哈希)
SHARED_PASSWORD = "Rismed2026!"

INTERNAL_USERS = [
    {
        "username": "robert.zhang@rismedronxin.com",
        "email": "robert.zhang@rismedronxin.com",
        "role": "super_admin",
        "is_admin": True,
        "company_id": 1,
    },
    {
        "username": "robert.zhang@onemipham.com",
        "email": "robert.zhang@onemipham.com",
        "role": "super_admin",
        "is_admin": True,
        "company_id": 2,
    },
    {
        "username": "robert.zhang@mipham.ai",
        "email": "robert.zhang@mipham.ai",
        "role": "super_admin",
        "is_admin": True,
        "company_id": 3,
    },
]


def migrate_users_table(conn):
    """为 users 表添加 company_id 列（幂等）。"""
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cur.fetchall()]
    if "company_id" not in columns:
        print("📌 添加 users.company_id 列...")
        cur.execute("ALTER TABLE users ADD COLUMN company_id INTEGER REFERENCES companies(id)")
        conn.commit()
        print("   ✅ company_id 列已添加")
    else:
        print("   ✅ company_id 列已存在")


def seed_companies(conn):
    """更新三家公司详细信息（幂等）。"""
    cur = conn.cursor()
    for c in COMPANIES:
        cur.execute("SELECT id FROM companies WHERE id = ?", (c["id"],))
        existing = cur.fetchone()
        if existing:
            # 更新
            cur.execute("""
                UPDATE companies
                SET name = ?, short_name = ?, english_name = ?, english_short_name = ?,
                    industry = ?, internal_control_mode = ?, currency = ?,
                    tax_region = ?, email = ?, website = ?
                WHERE id = ?
            """, (
                c["name"], c["short_name"], c["english_name"], c["english_short_name"],
                c["industry"], c["internal_control_mode"], c["currency"],
                c["tax_region"], c["email"], c["website"],
                c["id"],
            ))
            print(f"   📝 更新公司 ID={c['id']}: {c['short_name']}")
        else:
            # 插入（使用指定 ID）
            cur.execute("""
                INSERT INTO companies (id, name, short_name, english_name, english_short_name,
                    industry, internal_control_mode, currency, tax_region, email, website,
                    subscription_status, module_set)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', 'pro')
            """, (
                c["id"], c["name"], c["short_name"], c["english_name"], c["english_short_name"],
                c["industry"], c["internal_control_mode"], c["currency"],
                c["tax_region"], c["email"], c["website"],
            ))
            print(f"   ➕ 创建公司 ID={c['id']}: {c['short_name']}")
    conn.commit()


def seed_users(conn):
    """预置三家公司的内部用户（幂等：已存在则更新密码）。"""
    cur = conn.cursor()
    password_hash = bcrypt.hashpw(SHARED_PASSWORD.encode(), bcrypt.gensalt()).decode()

    for u in INTERNAL_USERS:
        cur.execute("SELECT id FROM users WHERE username = ?", (u["username"],))
        existing = cur.fetchone()
        if existing:
            # 更新密码和公司关联
            cur.execute("""
                UPDATE users
                SET email = ?, password_hash = ?, role = ?, is_admin = ?, company_id = ?
                WHERE username = ?
            """, (
                u["email"], password_hash, u["role"], u["is_admin"],
                u["company_id"], u["username"],
            ))
            print(f"   🔄 更新用户: {u['username']} → 公司 {u['company_id']}")
        else:
            # 创建
            cur.execute("""
                INSERT INTO users (username, email, password_hash, role, is_admin, is_active, company_id)
                VALUES (?, ?, ?, ?, ?, 1, ?)
            """, (
                u["username"], u["email"], password_hash, u["role"], u["is_admin"],
                u["company_id"],
            ))
            print(f"   ➕ 创建用户: {u['username']} → 公司 {u['company_id']}")
    conn.commit()


def fix_legacy_users(conn):
    """给已有的老用户关联公司（若没有 company_id）。"""
    cur = conn.cursor()
    # 手机号用户 → 全关联到公司 1（或删除？保留但标记）
    cur.execute("UPDATE users SET company_id = 1 WHERE company_id IS NULL AND username NOT LIKE '%@%'")
    updated = cur.rowcount
    if updated:
        print(f"   📌 {updated} 个老用户的 company_id 设为 1 (利美融信资本)")
    conn.commit()


def verify(conn):
    """验证最终状态。"""
    print("\n" + "=" * 60)
    print("📋 最终验证")
    print("=" * 60)

    cur = conn.cursor()
    cur.execute("SELECT id, name, short_name, english_short_name FROM companies ORDER BY id")
    print("\n公司列表:")
    for row in cur.fetchall():
        print(f"   ID={row[0]}: {row[1]} | {row[3]}")

    cur.execute("SELECT id, username, email, role, company_id, is_admin FROM users ORDER BY id")
    print("\n用户列表:")
    for row in cur.fetchall():
        print(f"   ID={row[0]}: {row[1]} | cid={row[4]} | admin={row[5]}")

    # 验证密码
    print("\n密码验证:")
    for u in INTERNAL_USERS:
        cur.execute("SELECT password_hash FROM users WHERE username = ?", (u["username"],))
        row = cur.fetchone()
        if row:
            ok = bcrypt.checkpw(SHARED_PASSWORD.encode(), row[0].encode())
            print(f"   {u['username']}: {'✅ 密码正确' if ok else '❌ 密码不匹配'}")
        else:
            print(f"   {u['username']}: ❌ 用户不存在")


def main():
    print("🔧 利美融信资本 — 内部用户预置脚本\n")

    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        print("   请先启动后端 (uv run uvicorn app.main:app) 以创建数据库")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    try:
        migrate_users_table(conn)
        print()
        seed_companies(conn)
        print()
        seed_users(conn)
        print()
        fix_legacy_users(conn)
        print()
        verify(conn)
        print("\n✅ 内部用户预置完成！")
        print(f"\n   三家公司的登录凭据：")
        for u in INTERNAL_USERS:
            print(f"   📧 {u['username']}")
        print(f"   🔑 统一密码: {SHARED_PASSWORD}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
