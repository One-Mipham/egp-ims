"""一次性修复：重新编号重复的凭证号码，并初始化序列表。

用法：
    cd backend
    python fix_duplicate_voucher_nos.py

规则：
    - 按 (company_id, voucher_type, date 月份) 分组
    - 每组内按 id 升序重新分配序号 (1, 2, 3, ...)
    - 同步更新 voucher_sequences 表，确保后续新增凭证接着最大序号递增
    - 删除的凭证号留空，永不递补
"""

from app.database import SessionLocal, init_db
from app.models import Voucher, VoucherSequence


def fix():
    # 确保表存在
    init_db()

    db = SessionLocal()
    try:
        vouchers = db.query(Voucher).order_by(Voucher.id).all()
        if not vouchers:
            print("数据库中没有凭证，无需修复。")
            return

        prefix_map = {"receipt": "收字", "payment": "付字", "transfer": "转字"}

        # 按 (company_id, voucher_type, month) 分组重新编号
        groups: dict[tuple, list[Voucher]] = {}
        for v in vouchers:
            key = (v.company_id, v.voucher_type, v.date[:7])
            groups.setdefault(key, []).append(v)

        fixed = 0
        for (company_id, vtype, month_prefix), group in groups.items():
            prefix = prefix_map.get(vtype, "转字")
            month_str = month_prefix.replace("-", "")
            for seq, v in enumerate(group, start=1):
                new_no = f"{prefix}{month_str}-{seq:04d}"
                if v.voucher_no != new_no:
                    print(f"  #{v.id}: {v.voucher_no} → {new_no}  (date={v.date}, summary={v.summary[:30]})")
                    v.voucher_no = new_no
                    fixed += 1

            # 同步序列表：设为该组最大序号
            max_seq = len(group)
            seq_row = (
                db.query(VoucherSequence)
                .filter(
                    VoucherSequence.company_id == company_id,
                    VoucherSequence.voucher_type == vtype,
                    VoucherSequence.period == month_prefix,
                )
                .first()
            )
            if seq_row:
                seq_row.last_seq = max_seq
            else:
                db.add(
                    VoucherSequence(
                        company_id=company_id,
                        voucher_type=vtype,
                        period=month_prefix,
                        last_seq=max_seq,
                    )
                )

        if fixed == 0:
            print("所有凭证号码已正确，无需修复。")
        else:
            db.commit()
            print(f"\n修复完成：共修正 {fixed} 张凭证号码。")
    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    fix()
