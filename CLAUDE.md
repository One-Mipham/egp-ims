# CLAUDE.md

> **项目**: omc-project1 — 企业智能管理系统
> **版本**: 0.1.0
> **创建日期**: 2026-05-04
> **最后更新**: 2026-06-21 — 路径重组: omc-project1 → business-products/egp-ims
> **维护人**: One Mipham Corporation 技术委员会

本项目遵循母公司 [Rismed Ronxin Capital 开发治理规范](../../CLAUDE.md) 和 [One Mipham Corporation 开发规范](../CLAUDE.md)。

## 项目概述

面向中小型投资/咨询/技术开发/AI 企业的企业智能管理系统。覆盖会计、固定资产、应收应付、进销存、投资、人力资源、知识库等模块，支持多公司账套隔离、四级内控角色、反记账/反结账、月/季/半年/年报（含去年同期对比）。

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | Python 3.12+ / FastAPI / SQLAlchemy / SQLite |
| 前端 | Vue 3 / Vite / PrimeVue / Tailwind CSS |
| 部署 | Docker Compose |
| 认证 | JWT |

## 开发命令

**后端**:
```bash
cd backend
uv run uvicorn app.main:app --reload --port 8000
```

**前端**:
```bash
cd frontend
npm run dev
```

**Docker**:
```bash
docker compose up -d
```

## 项目结构

```
omc-project1/
├── docker-compose.yml
├── backend/
│   ├── pyproject.toml
│   └── app/
│       ├── main.py
│       ├── database.py
│       ├── models.py
│       ├── schemas.py
│       ├── auth.py
│       ├── seed.py
│       └── routers/
└── frontend/
    ├── package.json
    ├── vite.config.ts
    └── src/
```

## 关键约束

- 一级会计科目按国标预置，不可删除
- 编码规则：一级4位 + 二/三/四级各2位 = 最多10位
- 凭证状态：draft → approved → posted → closed（简化模式可跳过 approved）
- 不相容岗位分离按内控模式（simplified/standard/strict）执行
- 所有敏感操作必须写入 AuditLog
