"""FastAPI 入口."""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from fastapi import Depends

from app.database import engine, Base, SessionLocal, run_migrations
from app.routers import auth, users, companies, departments, accounts, vouchers, templates, periods, reports, audit, prints, permissions, cockpit, counterparties, persons, projects, investments, init_data, hr, fixed_assets, receivables, payables, inventory_trade, admin, servers, kb, expenses, contracts, bids, budget, board, taxes, gl, subscriptions, cashflow_items, system, audit_reports, todo, access_control
from app.auth import verify_company_isolation
from app.permissions import require_module
from app.middleware import rate_limit_middleware, security_headers_middleware
from app.seed import seed_account_mappings, seed_subscription_plans

Base.metadata.create_all(bind=engine)
run_migrations()

try:
    seed_account_mappings()
    seed_subscription_plans(SessionLocal())
except Exception:
    pass  # may fail on first boot before tables exist

app = FastAPI(title="One Mipham Finance", version="0.1.0")

# ── Security: CORS ──
# SaaS: app.mipham.ai + Vercel preview URLs; 本地 dev: localhost
ALLOWED_ORIGINS = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173,https://app.mipham.ai,https://*.vercel.app",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── Security: Rate limiting ──
app.middleware("http")(rate_limit_middleware)

# ── Security: Security headers ──
app.middleware("http")(security_headers_middleware)


@app.middleware("http")
async def company_isolation_middleware(request: Request, call_next):
    """全局中间件：强制跨公司数据隔离。

    对所有 /api/* 请求（排除认证路由），从 query params 或 body 中提取 company_id
    并与 JWT token 中的 company_id 校验。不匹配则返回 403。
    """
    if request.url.path.startswith("/api/auth") or request.url.path == "/api/health":
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return await call_next(request)

    token = auth_header[7:]

    # 1. Query params 中的 company_id
    qp_cid = request.query_params.get("company_id")
    if qp_cid is not None:
        try:
            verify_company_isolation(token, int(qp_cid))
        except Exception as e:
            return JSONResponse(status_code=403, content={"detail": str(e.detail)})

    # 2. POST/PUT/PATCH body 中的 company_id
    if request.method in ("POST", "PUT", "PATCH"):
        body = await request.body()
        if body:
            import json
            try:
                data = json.loads(body)
                body_cid = data.get("company_id")
                if body_cid is not None:
                    try:
                        verify_company_isolation(token, int(body_cid))
                    except Exception as e:
                        return JSONResponse(status_code=403, content={"detail": str(getattr(e, 'detail', '无权访问其他公司的数据'))})
            except (json.JSONDecodeError, ValueError):
                pass  # 非 JSON 请求体（如文件上传）跳过

        # 重新注入 body 以供下游路由使用
        async def receive():
            return {"type": "http.request", "body": body}
        request._receive = receive

    # 3. 订阅过期 → 只读锁定（写操作被阻止）
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        if qp_cid or (request.method in ("POST", "PUT", "PATCH") and body):
            cid = None
            if qp_cid:
                try:
                    cid = int(qp_cid)
                except ValueError:
                    pass
            elif body:
                import json as _json
                try:
                    cid = _json.loads(body).get("company_id")
                except Exception:
                    pass
            if cid:
                from app.database import SessionLocal
                from app.models import Company as _Company
                _db = SessionLocal()
                try:
                    _company = _db.query(_Company).filter(_Company.id == cid).first()
                    if _company and _company.subscription_status in ("expired", "past_due", "cancelled"):
                        _db.close()
                        return JSONResponse(status_code=402, content={"detail": "订阅已过期，系统处于只读模式。请续费后继续使用。"})
                finally:
                    _db.close()

    response = await call_next(request)
    return response

# 公开路由（无需模块权限）
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户管理"])
app.include_router(companies.router, prefix="/api/companies", tags=["公司账套"])
app.include_router(permissions.router, prefix="/api/permissions", tags=["权限管理"])
app.include_router(kb.router, prefix="/api/kb", tags=["知识库"])
app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["订阅与支付"])
app.include_router(system.router, prefix="/api/system", tags=["系统管理"])
app.include_router(audit_reports.router, prefix="/api/audit-reports", tags=["年度审计报告"])
app.include_router(todo.router, prefix="/api/todo", tags=["协同办公"])
app.include_router(access_control.router, prefix="/api/access-control", tags=["门禁管理"])

# 会计模块（会计/财务经理/总监/管理员）
_accounting = [Depends(require_module("accounting"))]
app.include_router(accounts.router, prefix="/api/accounts", tags=["科目管理"], dependencies=_accounting)
app.include_router(vouchers.router, prefix="/api/vouchers", tags=["凭证管理"], dependencies=_accounting)
app.include_router(templates.router, prefix="/api/templates", tags=["凭证模板"], dependencies=_accounting)
app.include_router(periods.router, prefix="/api/periods", tags=["会计期间"], dependencies=_accounting)
app.include_router(prints.router, prefix="/api/prints", tags=["打印模块"], dependencies=_accounting)
app.include_router(taxes.router, prefix="/api/taxes", tags=["税务管理"], dependencies=_accounting)
app.include_router(gl.router, prefix="/api/gl", tags=["总账"], dependencies=_accounting)

# 报表（会计/财务经理/总监/管理员）
_reports = [Depends(require_module("reports"))]
app.include_router(reports.router, prefix="/api/reports", tags=["报表中心"], dependencies=_reports)
app.include_router(cockpit.router, prefix="/api/cockpit", tags=["管理驾驶舱"], dependencies=_reports)

# 财务管理（财务经理/总监/管理员）
_finance = [Depends(require_module("finance"))]
app.include_router(budget.router, prefix="/api", tags=["预算管理"], dependencies=_finance)
app.include_router(investments.router, prefix="/api/investments", tags=["投资管理"], dependencies=_finance)
app.include_router(init_data.router, prefix="/api/investments/init", tags=["基础档案"], dependencies=_finance)

# 费用报销（含出纳/部门负责人）
_expenses = [Depends(require_module("expenses"))]
app.include_router(expenses.router, prefix="/api/expenses", tags=["费用报销"], dependencies=_expenses)

# 固定资产（会计/财务经理/管理员）
_assets = [Depends(require_module("assets"))]
app.include_router(fixed_assets.router, prefix="/api/fixed-assets", tags=["固定资产管理"], dependencies=_assets)

# 应收/应付
_ar = [Depends(require_module("receivables"))]
_ap = [Depends(require_module("payables"))]
app.include_router(receivables.router, prefix="/api/receivables", tags=["应收账款管理"], dependencies=_ar)
app.include_router(payables.router, prefix="/api/payables", tags=["应付账款管理"], dependencies=_ap)

# 进销存（会计/行政/管理员）
_inv = [Depends(require_module("inventory"))]
app.include_router(inventory_trade.router, prefix="/api/inventory-trade", tags=["进销存管理"], dependencies=_inv)

# 招投标（行政/管理员）
_bids = [Depends(require_module("bids"))]
app.include_router(bids.router, prefix="/api/bids", tags=["招投标管理"], dependencies=_bids)

# 合同管理
_ct = [Depends(require_module("contracts"))]
app.include_router(contracts.router, prefix="/api/contracts", tags=["合同管理"], dependencies=_ct)

# 人力资源
_hr = [Depends(require_module("hr"))]
app.include_router(hr.router, prefix="/api/hr", tags=["HR"], dependencies=_hr)

# 行政综合
_adm = [Depends(require_module("admin"))]
app.include_router(admin.router, prefix="/api/admin", tags=["行政综合管理"], dependencies=_adm)
app.include_router(departments.router, prefix="/api/departments", tags=["部门管理"], dependencies=_adm)
app.include_router(counterparties.router, prefix="/api/counterparties", tags=["往来单位"], dependencies=_adm)
app.include_router(persons.router, prefix="/api/persons", tags=["员工个人"], dependencies=_adm)
app.include_router(cashflow_items.router, prefix="/api/cashflow-items", tags=["现金流量项目"], dependencies=_accounting)
app.include_router(projects.router, prefix="/api/projects", tags=["项目管理"], dependencies=_adm)
app.include_router(servers.router, prefix="/api/servers", tags=["服务器管理"], dependencies=_adm)

# 董事办（仅总监/管理员）
_board = [Depends(require_module("board"))]
app.include_router(board.router, prefix="/api/board", tags=["董事办"], dependencies=_board)

# 审计日志（会计及以上）
app.include_router(audit.router, prefix="/api/audit", tags=["审计日志"], dependencies=_accounting)


@app.get("/api/health")
def health():
    return {"status": "ok"}
