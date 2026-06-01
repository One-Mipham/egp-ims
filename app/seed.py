"""初始化国标一级科目数据。"""
from sqlalchemy.orm import Session
from app.models import Account, Company, CashFlowItem

# 企业会计准则一级科目完整列表
LEVEL1_ACCOUNTS = [
    # 资产类
    ("1001", "库存现金", "asset", "debit"),
    ("1002", "银行存款", "asset", "debit"),
    ("1012", "其他货币资金", "asset", "debit"),
    ("1101", "交易性金融资产", "asset", "debit"),
    ("1121", "应收票据", "asset", "debit"),
    ("1122", "应收账款", "asset", "debit"),
    ("1123", "预付账款", "asset", "debit"),
    ("1131", "应收股利", "asset", "debit"),
    ("1132", "应收利息", "asset", "debit"),
    ("1221", "其他应收款", "asset", "debit"),
    ("1231", "坏账准备", "asset", "credit"),
    ("1403", "原材料", "asset", "debit"),
    ("1405", "库存商品", "asset", "debit"),
    ("1411", "周转材料", "asset", "debit"),
    ("1461", "融资租赁资产", "asset", "debit"),
    ("1511", "长期股权投资", "asset", "debit"),
    ("1521", "投资性房地产", "asset", "debit"),
    ("1601", "固定资产", "asset", "debit"),
    ("1602", "累计折旧", "asset", "credit"),
    ("1604", "在建工程", "asset", "debit"),
    ("1701", "无形资产", "asset", "debit"),
    ("1702", "累计摊销", "asset", "credit"),
    ("1711", "商誉", "asset", "debit"),
    ("1715", "长期待摊费用", "asset", "debit"),
    ("1801", "递延所得税资产", "asset", "debit"),
    ("1821", "合同履约成本", "asset", "debit"),
    ("1822", "合同取得成本", "asset", "debit"),
    ("1901", "待处理财产损溢", "asset", "debit"),
    # 负债类
    ("2001", "短期借款", "liability", "credit"),
    ("2101", "交易性金融负债", "liability", "credit"),
    ("2201", "应付票据", "liability", "credit"),
    ("2202", "应付账款", "liability", "credit"),
    ("2203", "预收账款", "liability", "credit"),
    ("2211", "应付职工薪酬", "liability", "credit"),
    ("2221", "应交税费", "liability", "credit"),
    ("2231", "应付利息", "liability", "credit"),
    ("2232", "应付股利", "liability", "credit"),
    ("2241", "其他应付款", "liability", "credit"),
    ("2501", "长期借款", "liability", "credit"),
    ("2701", "长期应付款", "liability", "credit"),
    ("2801", "预计负债", "liability", "credit"),
    ("2802", "递延所得税负债", "liability", "credit"),
    # 权益类
    ("4001", "实收资本", "equity", "credit"),
    ("4002", "资本公积", "equity", "credit"),
    ("4101", "盈余公积", "equity", "credit"),
    ("4103", "本年利润", "equity", "credit"),
    ("4104", "利润分配", "equity", "credit"),
    ("4201", "其他综合收益", "equity", "credit"),
    # 成本类
    ("5001", "生产成本", "cost", "debit"),
    ("5101", "制造费用", "cost", "debit"),
    ("5201", "劳务成本", "cost", "debit"),
    ("5301", "研发支出", "cost", "debit"),
    # 损益类
    ("6001", "主营业务收入", "profit_loss", "credit"),
    ("6051", "其他业务收入", "profit_loss", "credit"),
    ("6101", "公允价值变动损益", "profit_loss", "credit"),
    ("6111", "投资收益", "profit_loss", "credit"),
    ("6115", "其他收益", "profit_loss", "credit"),
    ("6301", "营业外收入", "profit_loss", "credit"),
    ("6401", "主营业务成本", "profit_loss", "debit"),
    ("6402", "其他业务成本", "profit_loss", "debit"),
    ("6403", "税金及附加", "profit_loss", "debit"),
    ("6601", "销售费用", "profit_loss", "debit"),
    ("6602", "管理费用", "profit_loss", "debit"),
    ("6603", "财务费用", "profit_loss", "debit"),
    ("6701", "资产减值损失", "profit_loss", "debit"),
    ("6711", "营业外支出", "profit_loss", "debit"),
    ("6801", "所得税费用", "profit_loss", "debit"),
    ("6901", "以前年度损益调整", "profit_loss", "debit"),
]


def seed_level1_accounts(db: Session, company_id: int):
    """为指定公司创建国标一级科目。"""
    for code, name, category, direction in LEVEL1_ACCOUNTS:
        existing = db.query(Account).filter(
            Account.company_id == company_id, Account.code == code
        ).first()
        if not existing:
            account = Account(
                company_id=company_id,
                code=code,
                name=name,
                level=1,
                parent_code=None,
                category=category,
                balance_direction=direction,
                is_system=True,
            )
            db.add(account)
    db.commit()


# 常用二级科目 — 管理费用（6602）明细
LEVEL2_ACCOUNTS = [
    ("660201", "管理费用-人员费用", 2, "6602", "profit_loss", "debit"),
    ("660202", "管理费用-办公费", 2, "6602", "profit_loss", "debit"),
    ("660203", "管理费用-差旅费", 2, "6602", "profit_loss", "debit"),
    ("660204", "管理费用-业务招待费", 2, "6602", "profit_loss", "debit"),
    ("660205", "管理费用-折旧费", 2, "6602", "profit_loss", "debit"),
    ("660206", "管理费用-摊销费", 2, "6602", "profit_loss", "debit"),
    ("660207", "管理费用-咨询费", 2, "6602", "profit_loss", "debit"),
    ("660208", "管理费用-租赁费", 2, "6602", "profit_loss", "debit"),
    ("660209", "管理费用-物业费", 2, "6602", "profit_loss", "debit"),
    ("660210", "管理费用-技术服务费", 2, "6602", "profit_loss", "debit"),
    ("660211", "管理费用-专利知识产权费用", 2, "6602", "profit_loss", "debit"),
    ("660299", "管理费用-其他", 2, "6602", "profit_loss", "debit"),
]


def seed_level2_accounts(db: Session, company_id: int):
    """为指定公司创建常用二级科目（仅限损益类明细）。"""
    for code, name, level, parent_code, category, direction in LEVEL2_ACCOUNTS:
        existing = db.query(Account).filter(
            Account.company_id == company_id, Account.code == code
        ).first()
        if not existing:
            account = Account(
                company_id=company_id,
                code=code,
                name=name,
                level=level,
                parent_code=parent_code,
                category=category,
                balance_direction=direction,
                is_system=False,
            )
            db.add(account)
    db.commit()


# ── 应交税费（2221）完整科目体系 ──
# 二级科目：增值税 + 其他税种；三级科目：应交增值税 10 个专栏
# 来源：基准数据 科目.xlsx + 国标补充

TAX_LEVEL2 = [
    # 增值税相关二级科目
    ("222101", "应交增值税", "2221"),
    ("222102", "未交增值税", "2221"),
    ("222103", "预交增值税", "2221"),
    ("222104", "待抵扣进项税额", "2221"),
    ("222105", "待认证进项税额", "2221"),
    ("222106", "待转销项税额", "2221"),
    ("222107", "增值税留抵税额", "2221"),
    # 补充：基准数据中缺少的增值税相关科目
    ("222108", "简易计税", "2221"),
    ("222109", "转让金融商品应交增值税", "2221"),
    ("222110", "代扣代交增值税", "2221"),
    # 其他税种
    ("222112", "应交资源税", "2221"),
    ("222113", "应交企业所得税", "2221"),
    ("222114", "应交土地增值税", "2221"),
    ("222115", "应交城市维护建设税", "2221"),
    ("222116", "应交房产税", "2221"),
    ("222117", "应交土地使用税", "2221"),
    ("222118", "应交车船使用税", "2221"),
    ("222119", "应交个人所得税", "2221"),
    ("222120", "应交教育费附加", "2221"),
    ("222121", "应交地方教育附加", "2221"),
    ("222123", "应交印花税", "2221"),
    ("222124", "应交消费税", "2221"),
]

TAX_LEVEL3 = [
    # 222101 应交增值税 — 10 个专栏（增值税纳税申报表标准栏次）
    ("22210101", "进项税额", "222101"),
    ("22210102", "销项税额抵减", "222101"),
    ("22210103", "已交税金", "222101"),
    ("22210104", "转出未交增值税", "222101"),
    ("22210105", "减免税款", "222101"),
    ("22210106", "销项税额", "222101"),
    ("22210107", "出口退税", "222101"),
    ("22210108", "进项税额转出", "222101"),
    ("22210109", "出口抵减内销产品应纳税额", "222101"),
    ("22210110", "转出多交增值税", "222101"),
]


def seed_tax_accounts(db: Session, company_id: int):
    """为指定公司创建 2221 应交税费完整科目体系（二/三级，幂等）。"""
    # 先确保一级科目存在
    parent = db.query(Account).filter(
        Account.company_id == company_id, Account.code == "2221"
    ).first()
    if not parent:
        parent = Account(
            company_id=company_id, code="2221", name="应交税费",
            level=1, parent_code=None, category="liability",
            balance_direction="credit", is_system=True,
        )
        db.add(parent)
        db.flush()

    # 二级科目
    for code, name, parent_code in TAX_LEVEL2:
        existing = db.query(Account).filter(
            Account.company_id == company_id, Account.code == code
        ).first()
        if not existing:
            db.add(Account(
                company_id=company_id, code=code, name=name,
                level=2, parent_code=parent_code, category="liability",
                balance_direction="credit", is_system=True,
            ))

    # 三级科目
    for code, name, parent_code in TAX_LEVEL3:
        existing = db.query(Account).filter(
            Account.company_id == company_id, Account.code == code
        ).first()
        if not existing:
            db.add(Account(
                company_id=company_id, code=code, name=name,
                level=3, parent_code=parent_code, category="liability",
                balance_direction="credit", is_system=False,
            ))

    db.commit()


# ── 职级预设数据 ──
POSITIONS_SEED = [
    (1, "董事长", 0), (1, "副董事长", 1), (1, "执行董事", 2), (1, "非执行董事", 3), (1, "独立董事", 4),
    (2, "监事会主席", 10), (2, "监事", 11), (2, "职工监事", 12),
    (3, "首席执行官", 20), (3, "首席财务官", 21), (3, "首席技术官", 22), (3, "运营总裁", 23),
    (3, "执行副总裁", 24), (3, "常务副总裁", 25), (3, "高级副总裁", 26), (3, "副总裁", 27), (3, "总裁助理", 28),
    (4, "部门总经理", 30), (4, "总监", 31),
    (5, "部门副总经理", 40), (5, "副总监", 41),
    (6, "高级经理", 50), (6, "经理", 51), (6, "副经理", 52),
    (7, "主管", 60), (7, "专员", 61),
]

def seed_hr_positions(db: Session, company_id: int):
    """为指定公司创建预设职级。"""
    from app.models import HrPosition
    for level, name, sort_order in POSITIONS_SEED:
        existing = db.query(HrPosition).filter(
            HrPosition.company_id == company_id, HrPosition.name == name
        ).first()
        if not existing:
            db.add(HrPosition(company_id=company_id, name=name, level=level, sort_order=sort_order))
    db.commit()


def seed_account_mappings():
    """预置投资交易→会计科目映射规则。"""
    from app.database import SessionLocal
    from app.models import AccountMapping

    db = SessionLocal()
    mappings = [
        ("buy", None, "1101", "1002", "{type} {name}"),
        ("sell", None, "1002", "1101", "{type} {name}"),
        ("dividend", None, "1002", "6111", "收到{name}分红"),
        ("interest", None, "1002", "6111", "收到{name}利息"),
        ("fair_value_up", None, "1101", "6101", "{name}公允价值上升"),
        ("fair_value_down", None, "6101", "1101", "{name}公允价值下降"),
        ("capital_call", None, "1511", "1002", "资本召唤-{name}"),
        ("distribution", None, "1002", "1511", "分配返还-{name}"),
        ("capital_call", None, "1511", "1002", "资本召唤-{name}"),
    ]
    for txn_type, invest_type, debit, credit, desc_tpl in mappings:
        existing = db.query(AccountMapping).filter(
            AccountMapping.transaction_type == txn_type,
            AccountMapping.investment_type == invest_type,
        ).first()
        if not existing:
            db.add(AccountMapping(
                transaction_type=txn_type,
                investment_type=invest_type,
                debit_account_code=debit,
                credit_account_code=credit,
                description_template=desc_tpl,
            ))
    db.commit()
    db.close()
    print("AccountMapping seed completed")


# ═══════════ KB 分类种子 ═══════════

KB_SEED_CATEGORIES = {
    "法律合规": [
        "公司法", "合同法", "证券法", "会计法", "税法",
        "知识产权", "数据合规", "劳动用工", "监管政策",
    ],
    "财务会计": [
        "会计准则", "审计方法", "税务筹划", "财务报告", "内部控制", "预算管理",
    ],
    "投资研究": [
        "市场分析", "行业研究", "交易策略", "投资备忘录", "风险管理",
    ],
    "技术工程": [
        "Python", "Linux/Shell", "TypeScript/JavaScript", "数据库",
        "DevOps/Docker/K8s", "架构决策(ADR)", "运维手册(Runbook)", "事后复盘(Postmortem)",
    ],
    "AI 平台与工具": [
        "Claude/Anthropic", "Codex/OpenAI", "Gemini/Google",
        "Mipham Code", "Mipham Engine", "其他 AI 工具",
    ],
    "AI 研究": [
        "研究论文", "模型文档", "AI 安全与对齐", "行业动态",
    ],
    "产品与项目": [
        "产品规格(PRD)", "项目复盘", "API 文档", "用户手册",
    ],
    "人力资源": [
        "入职指南", "培训材料", "公司制度", "行政模板",
    ],
}


def seed_kb_categories(db: Session, company_id: int = 1):
    """为指定公司创建 L1 + L2 分类（幂等：已存在则跳过）。"""
    from app.models import KbCategory
    existing = db.query(KbCategory).filter(
        KbCategory.company_id == company_id, KbCategory.is_system == True
    ).count()
    if existing > 0:
        return  # 已种子过

    sort = 0
    for l1_name, l2_names in KB_SEED_CATEGORIES.items():
        l1 = KbCategory(
            company_id=company_id, name=l1_name, parent_id=None,
            level=1, sort_order=sort, is_system=True,
        )
        db.add(l1)
        db.flush()  # 获取 l1.id

        for j, l2_name in enumerate(l2_names):
            l2 = KbCategory(
                company_id=company_id, name=l2_name, parent_id=l1.id,
                level=2, sort_order=j, is_system=False,
            )
            db.add(l2)

        sort += 1

    db.commit()
    print(f"  ✅ KB 分类已创建: {len(KB_SEED_CATEGORIES)} 个一级, {sum(len(v) for v in KB_SEED_CATEGORIES.values())} 个二级")


SUBSCRIPTION_PLANS = [
    {
        "name": "基础包",
        "slug": "basic",
        "description": "会计核心功能：科目/凭证/总账/报表/税务 + 应收应付 + 费用报销",
        "billing_cycle": "monthly",
        "price_cny": 299, "price_usd": 49,
        "modules": ["accounting", "receivables", "payables", "expenses"],
        "sort_order": 1,
    },
    {
        "name": "基础包-半年",
        "slug": "basic-semi",
        "description": "基础包半年付，享 9 折优惠",
        "billing_cycle": "semi_annual",
        "price_cny": 1614, "price_usd": 264,
        "modules": ["accounting", "receivables", "payables", "expenses"],
        "sort_order": 2,
    },
    {
        "name": "基础包-年付",
        "slug": "basic-annual",
        "description": "基础包年付，享 83 折优惠（¥299×12→¥2,990）",
        "billing_cycle": "annual",
        "price_cny": 2990, "price_usd": 490,
        "modules": ["accounting", "receivables", "payables", "expenses"],
        "sort_order": 3,
    },
    {
        "name": "进阶包",
        "slug": "advanced",
        "description": "基础包 + 财务管理 + 固定资产 + 进销存 + 合同管理",
        "billing_cycle": "monthly",
        "price_cny": 599, "price_usd": 99,
        "modules": ["accounting", "receivables", "payables", "expenses",
                     "finance", "assets", "inventory", "contracts"],
        "sort_order": 4,
    },
    {
        "name": "进阶包-半年",
        "slug": "advanced-semi",
        "description": "进阶包半年付，享 9 折优惠",
        "billing_cycle": "semi_annual",
        "price_cny": 3234, "price_usd": 534,
        "modules": ["accounting", "receivables", "payables", "expenses",
                     "finance", "assets", "inventory", "contracts"],
        "sort_order": 5,
    },
    {
        "name": "进阶包-年付",
        "slug": "advanced-annual",
        "description": "进阶包年付，享 83 折优惠（¥599×12→¥5,990）",
        "billing_cycle": "annual",
        "price_cny": 5990, "price_usd": 990,
        "modules": ["accounting", "receivables", "payables", "expenses",
                     "finance", "assets", "inventory", "contracts"],
        "sort_order": 6,
    },
    {
        "name": "专业包",
        "slug": "pro",
        "description": "进阶包 + 投资管理 + 人力资源 + 董事办 + 行政综合",
        "billing_cycle": "monthly",
        "price_cny": 999, "price_usd": 159,
        "modules": ["accounting", "receivables", "payables", "expenses",
                     "finance", "assets", "inventory", "contracts",
                     "investments", "hr", "board", "admin"],
        "sort_order": 7,
    },
    {
        "name": "专业包-半年",
        "slug": "pro-semi",
        "description": "专业包半年付，享 9 折优惠",
        "billing_cycle": "semi_annual",
        "price_cny": 5394, "price_usd": 858,
        "modules": ["accounting", "receivables", "payables", "expenses",
                     "finance", "assets", "inventory", "contracts",
                     "investments", "hr", "board", "admin"],
        "sort_order": 8,
    },
    {
        "name": "专业包-年付",
        "slug": "pro-annual",
        "description": "专业包年付，享 83 折优惠（¥999×12→¥9,990）",
        "billing_cycle": "annual",
        "price_cny": 9990, "price_usd": 1590,
        "modules": ["accounting", "receivables", "payables", "expenses",
                     "finance", "assets", "inventory", "contracts",
                     "investments", "hr", "board", "admin"],
        "sort_order": 9,
    },
    {
        "name": "招投标管理",
        "slug": "bidding",
        "description": "单模块：招标管理 + 投标管理 + 例外事项",
        "billing_cycle": "monthly",
        "price_cny": 199, "price_usd": 29,
        "modules": ["bids"],
        "sort_order": 10,
    },
    {
        "name": "知识库",
        "slug": "knowledge",
        "description": "单模块：企业知识库管理（知识库对所有用户免费开放）",
        "billing_cycle": "monthly",
        "price_cny": 0, "price_usd": 0,
        "modules": ["knowledge"],
        "sort_order": 11,
    },
    {
        "name": "企业买断版",
        "slug": "buyout-enterprise",
        "description": "全部 14 模块，一年更新+源码交付，自部署",
        "billing_cycle": "lifetime",
        "price_cny": 99900, "price_usd": 14900,
        "modules": ["accounting", "receivables", "payables", "expenses",
                     "finance", "assets", "inventory", "contracts",
                     "investments", "hr", "board", "admin", "bids", "knowledge"],
        "sort_order": 12,
    },
]


def seed_subscription_plans(db: Session):
    """初始化订阅套餐。"""
    from app.models import SubscriptionPlan
    for p in SUBSCRIPTION_PLANS:
        existing = db.query(SubscriptionPlan).filter(SubscriptionPlan.slug == p["slug"]).first()
        if not existing:
            db.add(SubscriptionPlan(**p))
    db.commit()


def seed_cashflow_items(db: Session, company_id: int):
    """初始化现金流量表项目映射（会企03表国标预设）。"""
    # (code, name, category_code, direction, debit_accounts, credit_accounts)
    CF_ITEMS = [
        # === 经营活动流入 ===
        ("CF01", "销售商品、提供劳务收到的现金", "op_sales", "inflow",
         "1001,1002", "1122,6001,6051,2203"),
        # === 经营活动流出 ===
        ("CF02", "支付给职工以及为职工支付的现金", "op_staff", "outflow",
         "2211", "1001,1002"),
        ("CF03", "支付的各项税费", "op_tax", "outflow",
         "2221", "1001,1002"),
        ("CF04", "支付其它与经营活动有关的现金", "op_other_out", "outflow",
         "6602,6603,2241,1221,6601", "1001,1002"),
        # === 投资活动流出 ===
        ("CF05", "购建固定资产、无形资产和其他长期资产所支付的现金", "inv_build", "outflow",
         "1601,1604,1701,1715", "1001,1002"),
        ("CF06", "投资支付的现金", "inv_pay", "outflow",
         "1503,1511,1101,1521", "1001,1002"),
        # === 筹资活动流入 ===
        ("CF07", "取得借款收到的现金", "fin_borrow", "inflow",
         "1001,1002", "2241,2001,2501"),
        ("CF08", "吸收投资收到的现金", "fin_invest", "inflow",
         "1001,1002", "4001,4002"),
    ]

    existing = {cfi.code for cfi in db.query(CashFlowItem).filter(
        CashFlowItem.company_id == company_id
    ).all()}

    added = 0
    for code, name, cat_code, direction, dr_accts, cr_accts in CF_ITEMS:
        if code not in existing:
            db.add(CashFlowItem(
                company_id=company_id,
                code=code,
                name=name,
                category_code=cat_code,
                direction=direction,
                debit_accounts=dr_accts,
                credit_accounts=cr_accts,
                is_active=True,
            ))
            added += 1

    if added:
        db.commit()
        print(f"  ✓ Seeded {added} cash flow items for company {company_id}")


if __name__ == "__main__":
    from app.database import SessionLocal
    db = SessionLocal()
    company = db.query(Company).first()
    company_id = company.id if company else 1
    companies = db.query(Company).all()
    for c in companies:
        seed_level1_accounts(db, c.id)
        seed_level2_accounts(db, c.id)
        seed_tax_accounts(db, c.id)
        seed_cashflow_items(db, c.id)
        seed_hr_positions(db, c.id)
    seed_kb_categories(db, company_id)
    seed_subscription_plans(db)
    db.close()
    seed_account_mappings()
    print("Done.")
