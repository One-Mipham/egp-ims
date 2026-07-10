"""税务管理端点测试."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_declarations_empty():
    """列表查询 — 无认证返回401"""
    resp = client.get("/api/taxes/declarations?company_id=1")
    assert resp.status_code == 401


def test_list_invoices_empty():
    """发票列表 — 无认证返回401"""
    resp = client.get("/api/taxes/invoices?company_id=1")
    assert resp.status_code == 401


def test_declaration_crud_unauthorized():
    """申报 CRUD — 无认证拒绝"""
    resp = client.post(
        "/api/taxes/declarations",
        json={
            "company_id": 1,
            "tax_type": "vat",
            "period_start": "2026-01-01",
            "period_end": "2026-01-31",
            "tax_amount": 1000.0,
            "status": "pending",
        },
    )
    assert resp.status_code == 401

    resp = client.get("/api/taxes/declarations/1")
    assert resp.status_code == 401

    resp = client.put("/api/taxes/declarations/1", json={"tax_amount": 2000.0})
    assert resp.status_code == 401

    resp = client.delete("/api/taxes/declarations/1")
    assert resp.status_code == 401


def test_invoice_crud_unauthorized():
    """发票 CRUD — 无认证拒绝"""
    resp = client.post(
        "/api/taxes/invoices",
        json={
            "company_id": 1,
            "invoice_type": "sales",
            "invoice_number": "INV-001",
            "invoice_date": "2026-01-15",
            "amount": 10000.0,
            "tax_rate": 13.0,
            "tax_amount": 1300.0,
            "total_amount": 11300.0,
        },
    )
    assert resp.status_code == 401

    resp = client.get("/api/taxes/invoices/1")
    assert resp.status_code == 401

    resp = client.put("/api/taxes/invoices/1", json={"amount": 20000.0})
    assert resp.status_code == 401

    resp = client.delete("/api/taxes/invoices/1")
    assert resp.status_code == 401


def test_summary_endpoints():
    """汇总端点 — 端点可用"""
    resp = client.get("/api/taxes/declarations/summary?company_id=1")
    assert resp.status_code == 401

    resp = client.get("/api/taxes/invoices/summary?company_id=1")
    assert resp.status_code == 401


def test_all_12_endpoints_registered():
    """验证 12 个端点已注册"""
    routes = [r.path for r in app.routes if hasattr(r, "path")]
    tax_routes = [r for r in routes if "/api/taxes" in r]

    expected = [
        "/api/taxes/declarations",
        "/api/taxes/declarations/summary",
        "/api/taxes/declarations/{declaration_id}",
        "/api/taxes/invoices",
        "/api/taxes/invoices/summary",
        "/api/taxes/invoices/{invoice_id}",
    ]
    for path in expected:
        assert path in tax_routes, f"Missing route: {path}"
