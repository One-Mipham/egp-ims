# KB 分类体系重构设计

> 版本: 0.1.0 | 日期: 2026-05-22 | 状态: 已确认

## 一、背景

当前 KB 模块使用扁平字符串分类（10 个硬编码值），无层级、无权限控制。参照黑石/Jane Street/四大会计师事务所/OpenAI/Anthropic 知识库结构，对标会计科目编码体系，重构为多层级树形分类，逐级授权管理。

## 二、数据模型

### 2.1 新表 `kb_categories`

```python
class KbCategory(Base):
    __tablename__ = "kb_categories"
    id            = Column(Integer, primary_key=True)
    company_id    = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name          = Column(String(100), nullable=False)          # 分类名称
    parent_id     = Column(Integer, ForeignKey("kb_categories.id"), nullable=True)
    level         = Column(Integer, nullable=False, default=1)   # 自动计算
    sort_order    = Column(Integer, nullable=False, default=0)
    is_system     = Column(Boolean, nullable=False, default=False) # L1=true，不可删除
    is_active     = Column(Boolean, nullable=False, default=True)
    created_by    = Column(Integer, ForeignKey("users.id"))
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### 2.2 修改 `kb_articles`

| 字段 | 变更 |
|------|------|
| `category` (String(30)) | 移除 |
| `category_id` (FK → kb_categories.id) | 新增 |

现有数据迁移：根据旧 `category` 字符串匹配到新分类 ID。

## 三、权限模型

| 层级 | 管理者 | 权限 |
|------|--------|------|
| L1 | 系统管理员 | 预置 `is_system=true`，不可编辑删除 |
| L2 | 部门负责人 | 在 L1 下增删改子类 |
| L3+ | 员工 | 在父级下自由增删子类 |

**删除规则：**
- 删除需上级批准：操作人必须是目标分类父级的管理者
- 有子分类的分类不能删除（先清空子节点）
- 有文章的分类不能删除（先迁移或删除文章）
- L1 分类不可删除（`is_system=true`）

## 四、种子数据 — 8 个一级 + 46 个二级

所有一级均为 `is_system=true`，二级也预置作为启动基础。

### 1. 法律合规 `legal`
- 公司法、合同法、证券法、会计法、税法
- 知识产权、数据合规、劳动用工、监管政策

### 2. 财务会计 `finance`
- 会计准则(CAS/IFRS/GAAP)、审计方法、税务筹划
- 财务报告、内部控制、预算管理

### 3. 投资研究 `investment`
- 市场分析、行业研究、交易策略、投资备忘录、风险管理

### 4. 技术工程 `engineering`
- Python、Linux/Shell、TypeScript/JavaScript、数据库
- DevOps/Docker/K8s、架构决策(ADR)、运维手册(Runbook)、事后复盘(Postmortem)

### 5. AI 平台与工具 `ai-platforms`
- Claude/Anthropic、Codex/OpenAI、Gemini/Google
- Mipham Code、Mipham Engine、其他 AI 工具

### 6. AI 研究 `ai-research`
- 研究论文、模型文档、AI 安全与对齐、行业动态

### 7. 产品与项目 `products`
- 产品规格(PRD)、项目复盘、API 文档、用户手册

### 8. 人力资源 `hr`
- 入职指南、培训材料、公司制度、行政模板

## 五、API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/kb/categories` | 获取分类树（树形 JSON） |
| GET | `/kb/categories/{id}` | 获取单个分类 |
| POST | `/kb/categories` | 创建子分类（需验证父级权限） |
| PUT | `/kb/categories/{id}` | 编辑分类名称/排序 |
| DELETE | `/kb/categories/{id}` | 删除（需权限 + 子节点/文章检查） |

### 5.1 分类树返回格式

```json
[
  {
    "id": 1, "name": "法律合规", "level": 1, "is_system": true,
    "children": [
      { "id": 2, "name": "公司法", "level": 2, "is_system": false, "children": [] },
      { "id": 3, "name": "合同法", "level": 2, "is_system": false, "children": [
        { "id": 50, "name": "合同审查清单", "level": 3, "children": [] }
      ]}
    ]
  }
]
```

### 5.2 文章端点变更

- `GET /kb/articles` → `category` 参数改为 `category_id: int`
- `KbArticleCreate/Update` → `category` 字段改为 `category_id: int`
- `KbArticleResponse` → 返回 `category_id` + `category_name` + `category_path`

## 六、前端变更

### 6.1 左侧分类树
- 替换当前扁平列表为 PrimeVue Tree 组件
- L1 节点显示 🔒 锁图标
- 支持无限层级展开/折叠
- L2+ 根据角色显示 `+` 按钮添加子类

### 6.2 文章表单
- `category` 下拉改为树形选择器（TreeSelect）
- 文章列表显示完整路径如 `法律合规 > 合同法 > 合同审查清单`

### 6.3 分类管理对话框
- 编辑分类名称、排序
- 删除确认弹窗，显示子分类/文章数量
- 权限不足时 toast 提示"需上级批准"

## 七、自检清单

- [ ] 无 TBD/占位符 — PASS
- [ ] 内部无矛盾 — PASS
- [ ] 范围适中，单个 plan 可执行 — PASS
- [ ] 无不明确需求 — PASS（删除审批链已明确：操作人需为父级管理者，有子节点/文章禁止删除）
