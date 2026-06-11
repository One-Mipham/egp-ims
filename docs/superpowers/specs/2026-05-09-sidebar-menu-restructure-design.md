# 侧边栏菜单重构设计

> **日期**: 2026-05-09
> **状态**: 已确认
> **维护人**: 技术委员会

## 1. 目标

将侧边栏一级菜单从当前按功能模块平铺的结构，重构为 5 大管理系统分类的结构。一级菜单直接显示，二级菜单为下拉展开，三级菜单（子菜单）保持现有下拉逻辑。

## 2. 菜单结构

```yaml
一、人力资源管理系统:
  icon: pi-users
  items:
    - 1.0 公司人力资源管理制度 → /finance/hr/policy (占位)
    - 1.1 员工入职 → /finance/hr/onboarding (占位)
    - 1.2 员工培训 → /finance/hr/training (占位)
    - 1.3 员工考核 → /finance/hr/evaluation (占位)
    - 1.4 薪酬管理 → /finance/hr/compensation (占位)
    - 1.5 员工奖惩 → /finance/hr/rewards (占位)
    - 1.6 员工离职 → /finance/hr/offboarding (占位)
    - 1.7 人力资源预算管理 → /finance/hr/budget (占位)

二、行政综合管理系统:
  icon: pi-building
  items:
    - 2.1 文件管理 → /finance/admin/documents (占位)
    - 2.2 车辆管理 → /finance/admin/vehicles (占位)
    - 2.3 财产保险 → /finance/admin/insurance (占位)
    - 2.4 门禁管理 → /finance/admin/access (占位)
    - 2.5 资产与仓库管理 → /finance/inventory (原移动仓管功能迁移)

三、会计管理系统:
  icon: pi-book
  items:
    - 3.0 会计管理驾驶舱 → /finance/cockpit/accounting
      权限: accountant, finance_manager, finance_director, super_admin
      无权限: 菜单项灰色+锁定图标
    - 3.1 基础设置:
        - 公司信息
        - 科目
        - 凭证类别
        - 常用凭证
        - 常用摘要
        - 现金流量项目
        - 收付信息
    - 3.2 总账 → /finance/gl/vouchers
    - 3.3 进销存管理 → /finance/inventory-trade (占位)
    - 3.4 应收账款 → /finance/receivables (占位)
    - 3.5 应付账款 → /finance/payables (占位)
    - 3.6 固定资产管理 → /finance/fixed-assets (占位)
    - 3.7 税务管理:
        - 发票管理 (销项/进项/查询统计)
        - 附加税管理
        - 财产行为税
        - 税务报表
    - 3.8 投资管理 → /finance/investments/contracts
    - 3.9 报表中心 → /finance/reports
    - 3.10 协同办公 → /finance/collaboration (占位)
    - 3.11 系统设置 → /finance/settings/company

四、财务管理系统:
  icon: pi-chart-line
  items:
    - 4.0 财务管理驾驶舱 → /finance/cockpit/finance
      权限: finance_manager, finance_director, super_admin
      无权限: 菜单项灰色+锁定图标
    - 4.1 预算管理与绩效评价 → /finance/cockpit/budget (现有)
    - 4.2 现金流计划与融资计划 → /finance/cockpit/cashflow (现有)
    - 4.3 经营分析指标 → /finance/cockpit/indicators (现有)

五、董事办工作:
  icon: pi-briefcase
  items:
    - 5.1 董事会工作条例 → /finance/board/bylaws (占位)
    - 5.2 董事会专业委员会:
        - 提名委员会 → /finance/board/committees/nomination (占位)
        - 薪酬与绩效考核委员会 → /finance/board/committees/compensation (占位)
        - 战略发展委员会 → /finance/board/committees/strategy (占位)
        - 审计与稽核委员会 → /finance/board/committees/audit (占位)
    - 5.3 董秘工作职责 → /finance/board/secretary (占位)
    - 5.4 交易所工作对接 → /finance/board/exchange (占位)
    - 5.5 证监会、局工作对接 → /finance/board/csrc (占位)
    - 5.6 财务报告 → /finance/board/financial-reports (占位)
    - 5.7 股东管理 → /finance/board/shareholders (占位)
    - 5.8 投资者关系管理 → /finance/board/investors (占位)
    - 5.9 政府关系管理 → /finance/board/government (占位)
    - 5.10 媒体关系管理 → /finance/board/media (占位)
```

## 3. 组件架构

```
App.vue
├── SidebarMenu.vue          (NEW - 从 App.vue 提取)
│   ├── menuConfig.ts        (NEW - 菜单数据配置)
│   ├── SidebarHeader        (inline - logo + marquee)
│   └── SidebarFooter        (inline - user info + logout)
├── TopBar.vue               (breadcrumb + user)
└── <router-view>
    ├── Dashboard.vue        (MODIFIED - 精简为摘要首页)
    ├── AccountingCockpit.vue(NEW - 会计驾驶舱)
    ├── FinanceCockpit.vue   (NEW - 财务驾驶舱)
    └── PlaceholderPage.vue  (EXISTING - 占位页面)
```

## 4. 文件变更清单

| 操作 | 文件 | 说明 |
|------|------|------|
| NEW | `frontend/src/config/menuConfig.ts` | 5 大模块菜单数据，含权限标记 |
| NEW | `frontend/src/components/SidebarMenu.vue` | 侧边栏菜单组件（三级嵌套逻辑） |
| NEW | `frontend/src/views/AccountingCockpit.vue` | 会计驾驶舱（6 方框） |
| NEW | `frontend/src/views/FinanceCockpit.vue` | 财务驾驶舱（3 菜单 + 6 红绿灯） |
| MODIFY | `frontend/src/App.vue` | 删除 menuSections，引入 SidebarMenu |
| MODIFY | `frontend/src/views/Dashboard.vue` | 精简为摘要首页 |
| MODIFY | `frontend/src/router/index.ts` | 新增驾驶舱路由 + 占位路由 |

## 5. 权限规则

| 目标 | 允许角色 |
|------|----------|
| 会计管理驾驶舱 (3.0) | `accountant`, `finance_manager`, `finance_director`, `super_admin` |
| 财务管理驾驶舱 (4.0) | `finance_manager`, `finance_director`, `super_admin` |

无权限用户：菜单项可见但灰色 + 锁定图标，点击弹出 Toast "您无权访问此驾驶舱"。
路由层面同时加守卫，无权限返回 403。

## 6. 现有功能保留

- 现有会计相关路由（总账、报表、税务、投资、设置等）全部保留，路径不变
- 原"移动仓管"功能迁移至"二、行政综合管理系统 → 2.5 资产与仓库管理"
- 现有 Cockpit API `/cockpit/cockpit-lights` 继续使用
- 所有现有业务逻辑不变

## 7. 后续跨模块依赖（备忘，不在本次范围）

- 员工数据库 → HR 模块开发时建为全局共享实体
- 薪酬预算 → HR 模块薪酬数据需与财务模块预算表可互相引用
- 职位数据库 → 人力资源模块维护，其他模块引用
