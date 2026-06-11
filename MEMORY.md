# MEMORY.md — omc-project1

> 自动记忆文件，记录项目关键上下文，供 AI 助手恢复对话时使用。
> 最后更新: 2026-05-21

## 项目概况

企业智能管理系统（FastAPI + Vue 3 + PrimeVue + SQLite），15 个模块已基本实现：
- 人力资源、行政综合、招投标、投资管理、合同管理
- 固定资产、进销存、应收/应付账款、费用报销
- 会计管理（含税务、报表、总账）、财务管理（含预算驾驶舱）
- **新增：董事办工作**（驾驶舱、合规报送、内部报批、三会决议、股东名册、档案管理、对接日志）
- 知识库管理

## 关键路径

- 后端入口: `backend/app/main.py`
- 前端API基址: `frontend/src/api/index.ts` → `/finance/api`
- 前端路由: `frontend/src/router/index.ts`
- 菜单配置: `frontend/src/config/menuConfig.ts`
- 数据模型: `backend/app/models.py`

## 最近变更

### 2026-05-21 — 董事办模块 (fdfee8b)
- 新增 `BoardFiling` + `BoardShareholder` 模型
- schemas: `backend/app/schemas/board.py`
- router: `backend/app/routers/board.py` (cockpit-lights + CRUD)
- 4 个新视图: BoardCockpit, BoardPolicy, BoardFiling, BoardShareholder
- BoardFiling 按 doc_type 区分 5 种场景，含证监会/交易所下拉菜单
- 预算管理模块同步提交 (BudgetCockpit, HrBudget, budget API)

## 待办事项

- [ ] 会计管理系统 未完成项排查
- [ ] 全链路测试（各模块 CRUD + 角色权限）
- [ ] 审批流程柔性化：确保所有审批环节非强制，防止卡流程
- [ ] 全局 UI/UX 设计规范统一（字体、间距、表格、A4 打印、暗纹背景）
- [ ] 费用报销：借款 → 报销 → 冲抵 闭环测试
- [ ] 固定资产：购入 → 折旧 → 处置 闭环测试
