# KB 分类体系重构 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 KB 模块从扁平字符串分类重构为自引用树形层级分类（对标会计科目体系），L1 系统预置不可删，L2+ 逐级授权管理。

**Architecture:** 新增 `kb_categories` 自引用表（parent_id），`kb_articles.category` 改为 `category_id` FK。后端扩展 `routers/kb.py` 增加分类 CRUD 端点 + 权限校验。前端用递归组件渲染树形分类，TreeSelect 选择器替代下拉框。

**Tech Stack:** Python 3.12+ / FastAPI / SQLAlchemy / SQLite | Vue 3 / Tailwind CSS

---

## File Map

| 文件 | 操作 | 职责 |
|------|------|------|
| `backend/app/models.py` | 修改 | 新增 KbCategory，KbArticle 加 category_id |
| `backend/app/schemas/__init__.py` | 修改 | 新增 KbCategory 响应 schema，KbArticle 字段更新 |
| `backend/app/routers/kb.py` | 重写 | 分类 CRUD + 文章端点适配 category_id |
| `backend/app/seed.py` | 修改 | 种子 L1+L2 分类 |
| `frontend/src/api/index.ts` | 修改 | 新增分类 API，更新文章 API |
| `frontend/src/views/KnowledgeBase.vue` | 重写 | 树形分类 + 树选择器 + 分类管理 |

---

### Task 1: KbCategory 模型 + 迁移

**Files:**
- Modify: `backend/app/models.py:1287`（KbArticle 之后插入）
- Modify: `backend/app/database.py:27`（添加迁移 SQL）

- [ ] **Step 1: 在 models.py 新增 KbCategory 模型，KbArticle 追加 category_id 列**

```python
# 在 KbArticle 类后面、ExpenseReport 前面插入

class KbCategory(Base):
    __tablename__ = "kb_categories"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(100), nullable=False, comment="分类名称")
    parent_id = Column(Integer, ForeignKey("kb_categories.id"), nullable=True)
    level = Column(Integer, nullable=False, default=1, comment="层级深度 1/2/3...")
    sort_order = Column(Integer, nullable=False, default=0)
    is_system = Column(Boolean, nullable=False, default=False, comment="系统预置不可删")
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

同时在 KbArticle 类的 `category` 行后追加新字段：

```python
# 在 KbArticle 类的 category 行后追加:
    category_id = Column(Integer, ForeignKey("kb_categories.id"), nullable=True, comment="分类ID（新树形结构）")
```

- [ ] **Step 2: 在 database.py run_migrations() 添加建表和加列 SQL**

```python
# 在 migrations 列表末尾追加:
"CREATE TABLE IF NOT EXISTS kb_categories (id INTEGER PRIMARY KEY AUTOINCREMENT, company_id INTEGER NOT NULL REFERENCES companies(id), name VARCHAR(100) NOT NULL, parent_id INTEGER REFERENCES kb_categories(id), level INTEGER NOT NULL DEFAULT 1, sort_order INTEGER NOT NULL DEFAULT 0, is_system BOOLEAN NOT NULL DEFAULT 0, is_active BOOLEAN NOT NULL DEFAULT 1, created_by INTEGER REFERENCES users(id), created_at TIMESTAMP, updated_at TIMESTAMP)",
"ALTER TABLE kb_articles ADD COLUMN category_id INTEGER REFERENCES kb_categories(id)",
```

- [ ] **Step 3: 重启后端验证表创建成功**

```bash
cd backend && uv run python -c "from app.database import init_db, run_migrations; init_db(); run_migrations(); print('OK')"
```
Expected: `OK`（无异常）

- [ ] **Step 4: Commit**

```bash
git add backend/app/models.py backend/app/database.py
git commit -m "feat(kb): add KbCategory model + migration for hierarchical categories"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```


### Task 2: KbCategory Schemas + KbArticle Schema 更新

**Files:**
- Modify: `backend/app/schemas/__init__.py:1282`（KbArticleResponse 之后）

- [ ] **Step 1: 新增 KbCategory 相关 schema，修改 KbArticle schemas**

在 `KbArticleResponse` 之后插入：

```python
# ═══════════ 知识库分类 Schemas ═══════════

class KbCategoryCreate(BaseModel):
    company_id: int
    name: str
    parent_id: int

class KbCategoryUpdate(BaseModel):
    name: Optional[str] = None
    sort_order: Optional[int] = None

class KbCategoryResponse(BaseModel):
    id: int; company_id: int; name: str
    parent_id: Optional[int] = None; level: int = 1
    sort_order: int = 0; is_system: bool = False
    is_active: bool = True; created_by: Optional[int] = None
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}

class KbCategoryTreeNode(BaseModel):
    id: int; name: str; level: int; is_system: bool = False
    sort_order: int = 0; article_count: int = 0
    children: list["KbCategoryTreeNode"] = []
    model_config = {"from_attributes": True}
```

修改 `KbArticleCreate`（line 1261-1267），将 `category: str = "inbox"` 改为 `category_id: int`：

```python
class KbArticleCreate(BaseModel):
    company_id: int
    title: str
    content_md: Optional[str] = None
    category_id: int
    tags: list[str] = []
    status: str = "draft"
```

修改 `KbArticleUpdate`（line 1269-1274），将 `category: Optional[str] = None` 改为 `category_id: Optional[int] = None`：

```python
class KbArticleUpdate(BaseModel):
    title: Optional[str] = None
    content_md: Optional[str] = None
    category_id: Optional[int] = None
    tags: Optional[list[str]] = None
    status: Optional[str] = None
```

修改 `KbArticleResponse`（line 1276-1282），将 `category: str = "inbox"` 替换为 `category_id` + `category_name`：

```python
class KbArticleResponse(BaseModel):
    id: int; company_id: int; title: str
    content_md: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    tags: Optional[str] = None; author: Optional[str] = None
    status: str = "draft"; version: int = 1
    created_at: Optional[datetime] = None; updated_at: Optional[datetime] = None
    model_config = {"from_attributes": True}
```

- [ ] **Step 2: 验证 schema 无语法错误**

```bash
cd backend && uv run python -c "from app.schemas import KbCategoryCreate, KbCategoryUpdate, KbCategoryResponse, KbCategoryTreeNode, KbArticleCreate, KbArticleUpdate, KbArticleResponse; print('Schemas OK')"
```
Expected: `Schemas OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/__init__.py
git commit -m "feat(kb): add KbCategory schemas + update KbArticle schemas for category_id"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```


### Task 3: 分类 CRUD 端点

**Files:**
- Modify: `backend/app/routers/kb.py`（在现有代码基础上追加分类端点）

- [ ] **Step 1: 在 kb.py 顶部追加新 import，追加分类端点**

在现有 import 区域追加：

```python
from app.models import KbCategory
from app.schemas import KbCategoryCreate, KbCategoryUpdate, KbCategoryResponse, KbCategoryTreeNode
from sqlalchemy import func
```

删除旧的硬编码 `KB_CATEGORIES` 行（line 16）。

在 `list_categories()` 端点（line 131-144）处，替换为新的分类树端点和 CRUD：

```python
# ═══════════ 分类管理 ═══════════

def _build_tree(categories: list, article_counts: dict, parent_id: int | None = None) -> list[dict]:
    result = []
    for cat in categories:
        if cat.parent_id == parent_id:
            result.append({
                "id": cat.id, "name": cat.name, "level": cat.level,
                "is_system": cat.is_system, "sort_order": cat.sort_order,
                "article_count": article_counts.get(cat.id, 0),
                "children": _build_tree(categories, article_counts, cat.id),
            })
    result.sort(key=lambda x: (x["sort_order"], x["id"]))
    return result


@router.get("/categories")
def list_categories(
    company_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cats = db.query(KbCategory).filter(
        KbCategory.company_id == company_id,
        KbCategory.is_active == True,
    ).order_by(KbCategory.sort_order, KbCategory.id).all()

    article_counts = dict(
        db.query(KbArticle.category_id, func.count(KbArticle.id))
        .filter(KbArticle.company_id == company_id, KbArticle.category_id.in_([c.id for c in cats]))
        .group_by(KbArticle.category_id).all()
    )
    return _build_tree(cats, article_counts)


@router.get("/categories/{cat_id}", response_model=KbCategoryResponse)
def get_category(cat_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cat = db.query(KbCategory).filter(KbCategory.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    return cat


@router.post("/categories", response_model=KbCategoryResponse)
def create_category(
    data: KbCategoryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    parent = db.query(KbCategory).filter(KbCategory.id == data.parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="父分类不存在")
    cat = KbCategory(
        company_id=data.company_id,
        name=data.name.strip(),
        parent_id=data.parent_id,
        level=parent.level + 1,
        sort_order=0,
        is_system=False,
        created_by=user.id,
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    _audit(db, user, "create_category", cat.id, {"name": cat.name, "parent_id": data.parent_id})
    db.commit()
    return cat


@router.put("/categories/{cat_id}", response_model=KbCategoryResponse)
def update_category(
    cat_id: int,
    data: KbCategoryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cat = db.query(KbCategory).filter(KbCategory.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    if cat.is_system and (user.role not in ("super_admin",) and not user.is_admin):
        raise HTTPException(status_code=403, detail="系统预置分类不可编辑")
    if data.name is not None:
        cat.name = data.name.strip()
    if data.sort_order is not None:
        cat.sort_order = data.sort_order
    _audit(db, user, "update_category", cat.id, {"name": cat.name})
    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/categories/{cat_id}")
def delete_category(
    cat_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cat = db.query(KbCategory).filter(KbCategory.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    if cat.is_system:
        raise HTTPException(status_code=403, detail="系统预置分类不可删除")

    # 检查是否有子分类
    children = db.query(KbCategory).filter(KbCategory.parent_id == cat_id).count()
    if children > 0:
        raise HTTPException(status_code=400, detail="该分类下还有子分类，请先删除子分类")

    # 检查是否有文章
    article_count = db.query(KbArticle).filter(KbArticle.category_id == cat_id).count()
    if article_count > 0:
        raise HTTPException(status_code=400, detail=f"该分类下有 {article_count} 篇文章，请先迁移或删除文章")

    # 权限检查：L2 需 finance_manager+，L3+ 需本人或上级
    can_delete = user.is_admin or user.role in ("super_admin", "finance_director", "finance_manager") or cat.created_by == user.id
    if not can_delete:
        raise HTTPException(status_code=403, detail="需上级批准：只有部门负责人或创建人可以删除分类")

    _audit(db, user, "delete_category", cat.id, {"name": cat.name})
    db.delete(cat)
    db.commit()
    return {"ok": True}
```

- [ ] **Step 2: 验证端点可访问（需要后端运行中）**

```bash
curl -s http://localhost:8000/api/kb/categories?company_id=1 | head -c 200
```
Expected: JSON 数组（初始为空 `[]`）

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/kb.py
git commit -m "feat(kb): add hierarchical category CRUD endpoints with permission checks"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```


### Task 4: 文章端点适配 category_id

**Files:**
- Modify: `backend/app/routers/kb.py`（修改现有文章端点）

- [ ] **Step 1: 修改 list_articles 端点，category 参数改为 category_id**

在文件顶部（`router = APIRouter()` 之后）添加辅助函数：

```python
def _get_descendant_ids(all_cats: list, root_id: int) -> set[int]:
    """返回 root_id 及其所有后代的 ID 集合."""
    children_map: dict[int, list[int]] = {}
    for c in all_cats:
        if c.parent_id:
            children_map.setdefault(c.parent_id, []).append(c.id)
    result = {root_id}
    stack = [root_id]
    while stack:
        pid = stack.pop()
        for child_id in children_map.get(pid, []):
            if child_id not in result:
                result.add(child_id)
                stack.append(child_id)
    return result


def _article_dict(item: KbArticle, cat_map: dict[int, str]) -> dict:
    """将 KbArticle ORM 对象转为字典（含 category_name）."""
    return {
        "id": item.id, "company_id": item.company_id, "title": item.title,
        "content_md": item.content_md, "category_id": item.category_id,
        "category_name": cat_map.get(item.category_id) if item.category_id else None,
        "tags": item.tags, "author": item.author,
        "status": item.status, "version": item.version,
        "created_at": item.created_at, "updated_at": item.updated_at,
    }
```

将 `list_articles` 函数改为：

```python
@router.get("/articles")
def list_articles(
    company_id: int,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    category_id: int | None = None,
    status: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(KbArticle).filter(KbArticle.company_id == company_id)
    if category_id:
        all_cats = db.query(KbCategory).filter(
            KbCategory.company_id == company_id, KbCategory.is_active == True
        ).all()
        ids = _get_descendant_ids(all_cats, category_id)
        q = q.filter(KbArticle.category_id.in_(ids))
    if status:
        q = q.filter(KbArticle.status == status)
    if search:
        pattern = f"%{search}%"
        q = q.filter((KbArticle.title.ilike(pattern)) | (KbArticle.content_md.ilike(pattern)))
    items = q.order_by(KbArticle.updated_at.desc()).offset(offset).limit(limit).all()
    # 一次查询构建 category_name 映射，避免 N+1
    cat_ids = {i.category_id for i in items if i.category_id}
    cat_map = {}
    if cat_ids:
        cat_map = {c.id: c.name for c in db.query(KbCategory).filter(KbCategory.id.in_(cat_ids)).all()}
    return [_article_dict(item, cat_map) for item in items]
```

- [ ] **Step 2: 修改 create_article 端点**

```python
@router.post("/articles", response_model=KbArticleResponse)
def create_article(data: KbArticleCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not data.title.strip():
        raise HTTPException(status_code=400, detail="标题不能为空")
    # 验证 category_id 存在
    cat = db.query(KbCategory).filter(KbCategory.id == data.category_id).first()
    if not cat:
        raise HTTPException(status_code=400, detail="分类不存在")
    tags_str = ",".join(data.tags) if data.tags else None
    author_name = user.username
    item = KbArticle(**data.model_dump(exclude={"tags"}), tags=tags_str, version=1, author=author_name)
    db.add(item)
    db.commit()
    db.refresh(item)
    _audit(db, user, "create", item.id, {"title": item.title, "category_id": item.category_id})
    db.commit()
    cat_map = {cat.id: cat.name}
    return _article_dict(item, cat_map)
```

- [ ] **Step 3: 修改 update_article 端点**

```python
@router.put("/articles/{article_id}", response_model=KbArticleResponse)
def update_article(article_id: int, data: KbArticleUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(KbArticle).filter(KbArticle.id == article_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="文章不存在")
    update_data = data.model_dump(exclude_unset=True, exclude={"tags"})
    if "category_id" in update_data:
        cat = db.query(KbCategory).filter(KbCategory.id == update_data["category_id"]).first()
        if not cat:
            raise HTTPException(status_code=400, detail="分类不存在")
    if data.tags is not None:
        update_data["tags"] = ",".join(data.tags)
    for k, v in update_data.items():
        setattr(item, k, v)
    item.version += 1
    _audit(db, user, "update", item.id, {"title": item.title, "category_id": item.category_id, "version": item.version})
    db.commit()
    db.refresh(item)
    cat_map = {}
    if item.category_id:
        cat = db.query(KbCategory).filter(KbCategory.id == item.category_id).first()
        if cat:
            cat_map[item.category_id] = cat.name
    return _article_dict(item, cat_map)
```

- [ ] **Step 4: 修改 get_article 使用 _article_dict**

```python
@router.get("/articles/{article_id}")
def get_article(article_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(KbArticle).filter(KbArticle.id == article_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="文章不存在")
    cat_map = {}
    if item.category_id:
        cat = db.query(KbCategory).filter(KbCategory.id == item.category_id).first()
        if cat:
            cat_map[item.category_id] = cat.name
    return _article_dict(item, cat_map)
```

- [ ] **Step 5: 修改 CSV 导出端点（category → category_name）**

```python
@router.get("/articles/csv")
def export_articles_csv(
    company_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    items = db.query(KbArticle).filter(KbArticle.company_id == company_id).order_by(KbArticle.updated_at.desc()).all()
    cat_map = {c.id: c.name for c in db.query(KbCategory).filter(KbCategory.company_id == company_id).all()}
    output = io.StringIO()
    writer = csv_mod.writer(output)
    writer.writerow(["标题", "分类", "作者", "状态", "版本", "标签", "更新时间", "正文"])
    for i in items:
        cat_name = cat_map.get(i.category_id, "") if i.category_id else ""
        writer.writerow([i.title, cat_name, i.author or "", i.status, i.version, i.tags or "", (i.updated_at.strftime("%Y-%m-%d %H:%M") if i.updated_at else ""), (i.content_md or "")[:500]])
    output.seek(0)
    return StreamingResponse(io.BytesIO(output.getvalue().encode('utf-8-sig')), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=kb_articles.csv"})
```

同时需要将 KbArticle 的 `category` 字段从 models.py 中移除（或保留但标记废弃）。由于 SQLite 不支持 DROP COLUMN，保留旧列但不再使用：

```python
# 在 KbArticle 类中，将 category 行改为:
    category = Column(String(30), nullable=True, comment="[已废弃] 改用 category_id")
```

- [ ] **Step 6: 重启后端，用 curl 验证**

```bash
# 先验证列表
curl -s "http://localhost:8000/api/kb/articles?company_id=1&limit=3" | python -m json.tool | head -20
```
Expected: 返回文章列表，每条含 `category_id` 和 `category_name`

- [ ] **Step 7: Commit**

```bash
git add backend/app/routers/kb.py backend/app/models.py
git commit -m "feat(kb): adapt article endpoints to category_id with descendant query + response enrichment"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```


### Task 5: 种子数据 — 8 个 L1 + 46 个 L2

**Files:**
- Modify: `backend/app/seed.py`

- [ ] **Step 1: 在 seed.py 追加 KB 分类种子函数**

先在 seed.py 顶部确认已导入 KbCategory。找到 seed.py 中 KB 种子部分（如有），或在文件末尾追加：

```python

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
```

- [ ] **Step 2: 在 seed.py 的 main() 或主种子函数中调用**

找到 seed.py 中的种子主函数，在合适位置追加：

```python
    seed_kb_categories(db, company_id)
```

- [ ] **Step 3: 运行种子并验证**

```bash
cd backend && uv run python -m app.seed
```
Expected: 输出 `✅ KB 分类已创建: 8 个一级, 46 个二级`

```bash
curl -s http://localhost:8000/api/kb/categories?company_id=1 | python -m json.tool | head -40
```
Expected: 显示 8 个一级节点，各有 children

- [ ] **Step 4: Commit**

```bash
git add backend/app/seed.py
git commit -m "feat(kb): seed 8 L1 + 46 L2 categories with is_system protection"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```


### Task 6: 前端 API 函数更新

**Files:**
- Modify: `frontend/src/api/index.ts:585-597`

- [ ] **Step 1: 更新 KB API 函数**

```typescript
// ═══════════ 知识库管理 ═══════════
export const listKbArticles = (companyId: number, params?: { category_id?: number; status?: string; search?: string; limit?: number; offset?: number }) =>
    api.get('/kb/articles', { params: { company_id: companyId, ...params } })
export const getKbArticle = (id: number) =>
    api.get(`/kb/articles/${id}`)
export const createKbArticle = (data: any) =>
    api.post('/kb/articles', data)
export const updateKbArticle = (id: number, data: any) =>
    api.put(`/kb/articles/${id}`, data)
export const deleteKbArticle = (id: number) =>
    api.delete(`/kb/articles/${id}`)

// KB 分类
export const listKbCategories = (companyId: number) =>
    api.get('/kb/categories', { params: { company_id: companyId } })
export const getKbCategory = (id: number) =>
    api.get(`/kb/categories/${id}`)
export const createKbCategory = (data: { company_id: number; name: string; parent_id: number }) =>
    api.post('/kb/categories', data)
export const updateKbCategory = (id: number, data: { name?: string; sort_order?: number }) =>
    api.put(`/kb/categories/${id}`, data)
export const deleteKbCategory = (id: number) =>
    api.delete(`/kb/categories/${id}`)
```

- [ ] **Step 2: 验证无 TypeScript 编译错误**

```bash
cd frontend && npx vue-tsc --noEmit 2>&1 | head -10
```
Expected: 无新错误（可能有已有错误）

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/index.ts
git commit -m "feat(kb): update frontend API — category tree CRUD + article category_id param"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```


### Task 7: KnowledgeBase.vue — 分类树 + 文章列表适配

**Files:**
- Modify: `frontend/src/views/KnowledgeBase.vue`（重写 script 和 template 左侧栏）

由于改动较大（~340 行），这里分三个子任务：script 逻辑、左侧分类树、中右栏适配。

- [ ] **Step 1: 重写 `<script setup>` 部分**

完整替换 line 1-163 的 `<script setup>` 块为以下代码：

```vue
<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useToast } from 'primevue/usetoast'
import { marked } from 'marked'
import {
  listKbArticles, getKbArticle, createKbArticle, updateKbArticle, deleteKbArticle,
  listKbCategories, createKbCategory, updateKbCategory, deleteKbCategory,
} from '../api'

const toast = useToast()
const companyId = Number(localStorage.getItem('companyId') || '1')
const articles = ref<any[]>([])
const categoryTree = ref<any[]>([])
const selectedCategoryId = ref<number | null>(null)
const selectedArticle = ref<any>(null)
const searchText = ref('')
const editMode = ref(false)
const editorVisible = ref(false)
const page = ref(1)
const pageSize = 20
const selectedIds = ref<Set<number>>(new Set())

// 分类管理
const catDialogVisible = ref(false)
const catDialogMode = ref<'create' | 'edit'>('create')
const catForm = ref({ name: '', parent_id: 0 })
const editingCatId = ref<number | null>(null)
const expandedIds = ref<Set<number>>(new Set())

const emptyForm = () => ({
  company_id: companyId, title: '', content_md: '', category_id: 0,
  tags: [] as string[], status: 'draft',
})

const form = ref(emptyForm())
const tagInput = ref('')

const renderedHtml = computed(() => {
  if (!selectedArticle.value?.content_md) return '<p class="text-zinc-400 text-sm">暂无内容</p>'
  return marked(selectedArticle.value.content_md || '')
})

function findCatName(id: number): string {
  const find = (nodes: any[]): any => {
    for (const n of nodes) {
      if (n.id === id) return n
      if (n.children?.length) {
        const r = find(n.children)
        if (r) return r
      }
    }
    return null
  }
  return find(categoryTree.value)?.name || ''
}

function findCatPath(id: number): string {
  const find = (nodes: any[], ancestors: string[]): string | null => {
    for (const n of nodes) {
      if (n.id === id) return [...ancestors, n.name].join(' > ')
      if (n.children?.length) {
        const r = find(n.children, [...ancestors, n.name])
        if (r) return r
      }
    }
    return null
  }
  return find(categoryTree.value, []) || ''
}

async function loadCategories() {
  const { data } = await listKbCategories(companyId)
  categoryTree.value = data
  // 默认展开 L1
  data.forEach((n: any) => expandedIds.value.add(n.id))
}

async function loadArticles() {
  const params: Record<string, any> = { limit: pageSize, offset: (page.value - 1) * pageSize }
  if (selectedCategoryId.value) params.category_id = selectedCategoryId.value
  if (searchText.value) params.search = searchText.value
  const { data } = await listKbArticles(companyId, params)
  articles.value = data
}

function onSearch() { page.value = 1; selectedIds.value.clear(); loadArticles() }

async function selectArticle(article: any) {
  const { data } = await getKbArticle(article.id)
  selectedArticle.value = data
  editMode.value = false
}

function selectCategory(id: number) {
  selectedCategoryId.value = selectedCategoryId.value === id ? null : id
  selectedArticle.value = null
  page.value = 1
  loadArticles()
}

function toggleExpand(id: number) {
  if (expandedIds.value.has(id)) expandedIds.value.delete(id)
  else expandedIds.value.add(id)
}

// 分类管理
function openCreateCat(parentId: number) {
  catDialogMode.value = 'create'
  catForm.value = { name: '', parent_id: parentId }
  editingCatId.value = null
  catDialogVisible.value = true
}

function openEditCat(cat: any) {
  catDialogMode.value = 'edit'
  catForm.value = { name: cat.name, parent_id: cat.parent_id || 0 }
  editingCatId.value = cat.id
  catDialogVisible.value = true
}

async function saveCat() {
  if (!catForm.value.name.trim()) return
  try {
    if (catDialogMode.value === 'create') {
      await createKbCategory({ company_id: companyId, name: catForm.value.name.trim(), parent_id: catForm.value.parent_id })
      toast.add({ severity: 'success', summary: '分类已创建', life: 2000 })
    } else {
      await updateKbCategory(editingCatId.value!, { name: catForm.value.name.trim() })
      toast.add({ severity: 'success', summary: '分类已更新', life: 2000 })
    }
    catDialogVisible.value = false
    await loadCategories()
  } catch (e: any) {
    toast.add({ severity: 'error', summary: e?.response?.data?.detail || '操作失败', life: 3000 })
  }
}

async function removeCat(cat: any) {
  if (cat.is_system) {
    toast.add({ severity: 'warn', summary: '系统预置分类不可删除', life: 3000 })
    return
  }
  if (!confirm(`确定删除分类「${cat.name}」？`)) return
  try {
    await deleteKbCategory(cat.id)
    toast.add({ severity: 'success', summary: '已删除', life: 2000 })
    await loadCategories()
    // 如果当前选中该分类，清除
    if (selectedCategoryId.value === cat.id) { selectedCategoryId.value = null; loadArticles() }
  } catch (e: any) {
    toast.add({ severity: 'error', summary: e?.response?.data?.detail || '需上级批准', life: 3000 })
  }
}

function toggleSelectAll() {
  if (selectedIds.value.size === articles.value.length) { selectedIds.value.clear() }
  else { articles.value.forEach((a: any) => selectedIds.value.add(a.id)) }
}

function toggleSelect(id: number) {
  if (selectedIds.value.has(id)) selectedIds.value.delete(id)
  else selectedIds.value.add(id)
}

async function batchDelete() {
  if (selectedIds.value.size === 0) return
  if (!confirm(`确定删除选中的 ${selectedIds.value.size} 篇文章？`)) return
  await fetch('/api/kb/articles/batch-delete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('token')}` },
    body: JSON.stringify({ ids: Array.from(selectedIds.value) }),
  })
  toast.add({ severity: 'success', summary: `已删除 ${selectedIds.value.size} 篇`, life: 2000 })
  selectedIds.value.clear()
  await loadArticles()
}

function exportCSV() {
  const a = document.createElement('a')
  a.href = `/api/kb/articles/csv?company_id=${companyId}`
  a.download = '知识库文章.csv'
  a.click()
}

function openCreate() {
  form.value = emptyForm()
  if (selectedCategoryId.value) form.value.category_id = selectedCategoryId.value
  tagInput.value = ''
  editorVisible.value = true
}

function openEdit() {
  const a = selectedArticle.value
  form.value = {
    company_id: companyId,
    title: a.title,
    content_md: a.content_md || '',
    category_id: a.category_id || 0,
    tags: a.tags ? a.tags.split(',').filter(Boolean) : [],
    status: a.status,
  }
  editMode.value = true
  tagInput.value = ''
  editorVisible.value = true
}

function addTag() {
  const t = tagInput.value.trim()
  if (t && !form.value.tags.includes(t)) { form.value.tags.push(t); tagInput.value = '' }
}

function removeTag(t: string) { form.value.tags = form.value.tags.filter((x: string) => x !== t) }

async function save() {
  const payload = { ...form.value }
  if (selectedArticle.value && editMode.value) {
    await updateKbArticle(selectedArticle.value.id, payload)
    toast.add({ severity: 'success', summary: '已更新', life: 2000 })
  } else {
    await createKbArticle(payload)
    toast.add({ severity: 'success', summary: '文章已创建', life: 2000 })
  }
  editorVisible.value = false
  selectedArticle.value = null
  await loadArticles()
}

async function remove() {
  if (!selectedArticle.value || !confirm('确定删除该文章？')) return
  await deleteKbArticle(selectedArticle.value.id)
  toast.add({ severity: 'success', summary: '已删除', life: 2000 })
  selectedArticle.value = null
  await loadArticles()
}

async function togglePublish() {
  const a = selectedArticle.value
  const newStatus = a.status === 'published' ? 'draft' : 'published'
  await updateKbArticle(a.id, { status: newStatus })
  toast.add({ severity: 'success', summary: newStatus === 'published' ? '已发布' : '已取消发布', life: 2000 })
  await loadArticles()
  selectArticle({ id: a.id })
}

onMounted(async () => {
  await Promise.all([loadCategories(), loadArticles()])
})
</script>
```

- [ ] **Step 2: 重写 template 左侧分类树区域**

替换 line 168-190 的左侧栏：

```vue
    <!-- Left: Category Tree -->
    <div class="w-56 border-r border-dashed border-zinc-200 bg-zinc-50 flex flex-col shrink-0">
      <div class="p-3 border-b border-dashed border-zinc-200 space-y-2">
        <button @click="openCreate" class="w-full px-3 py-2 bg-blue-600 text-white rounded text-xs hover:bg-blue-700">
          + 新建文章
        </button>
        <button @click="exportCSV" class="w-full px-3 py-1.5 border rounded text-xs hover:bg-zinc-100">导出CSV</button>
        <button v-if="selectedIds.size > 0" @click="batchDelete" class="w-full px-3 py-1.5 border border-red-300 text-red-600 rounded text-xs hover:bg-red-50">
          删除选中 ({{ selectedIds.size }})
        </button>
      </div>
      <div class="overflow-auto flex-1">
        <!-- 递归分类树 -->
        <div v-for="cat in categoryTree" :key="cat.id">
          <CategoryTreeNode
            :cat="cat"
            :selected-id="selectedCategoryId"
            :expanded-ids="expandedIds"
            @select="selectCategory"
            @toggle="toggleExpand"
            @add="openCreateCat"
            @edit="openEditCat"
            @remove="removeCat"
          />
        </div>
        <div v-if="categoryTree.length === 0" class="p-4 text-center text-xs text-zinc-400">
          暂无分类
        </div>
      </div>
    </div>
```

- [ ] **Step 3: 中栏文章列表适配新的 category 字段**

修改 line 212 的 `categoryLabel(article.category)`：

```vue
              <span class="text-[10px] text-zinc-400">{{ findCatName(article.category_id) }}</span>
```

同样修改右侧预览栏 line 244 的 category 显示：

```vue
              <span>{{ findCatName(selectedArticle.category_id) }}</span>
```

- [ ] **Step 4: 文章编辑对话框中分类选择改为树形下拉**

替换 line 283-288 的分类 `<select>`：

```vue
            <div class="flex-1">
              <label class="text-xs text-zinc-500">分类</label>
              <select v-model="form.category_id" class="w-full border rounded px-2 py-1.5 text-sm">
                <option :value="0" disabled>请选择分类</option>
                <optgroup v-for="l1 in categoryTree" :key="l1.id" :label="l1.name">
                  <option :value="l1.id">{{ l1.name }}</option>
                  <template v-for="l2 in l1.children" :key="l2.id">
                    <option :value="l2.id">&nbsp;&nbsp;{{ l2.name }}</option>
                  </template>
                </optgroup>
              </select>
            </div>
```

- [ ] **Step 5: 验证前端运行**

```bash
cd frontend && npm run dev
```
打开浏览器确认：左侧显示树形分类，点击可筛选，可展开折叠

- [ ] **Step 6: Commit**

```bash
git add frontend/src/views/KnowledgeBase.vue
git commit -m "feat(kb): hierarchical category tree with recursive component + article form adaptation"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```


### Task 8: CategoryTreeNode 递归组件 + 分类管理对话框

**Files:**
- Create: `frontend/src/components/kb/CategoryTreeNode.vue`
- Modify: `frontend/src/views/KnowledgeBase.vue`（追加分类管理对话框 HTML）

- [ ] **Step 1: 创建递归树节点组件**

```vue
<script setup lang="ts">
defineProps<{
  cat: any
  selectedId: number | null
  expandedIds: Set<number>
  depth?: number
}>()

defineEmits<{
  select: [id: number]
  toggle: [id: number]
  add: [parentId: number]
  edit: [cat: any]
  remove: [cat: any]
}>()

const props = withDefaults(defineProps<{ depth?: number }>(), { depth: 0 })
</script>

<template>
  <div>
    <div
      class="flex items-center justify-between px-3 py-1.5 text-xs cursor-pointer hover:bg-zinc-100 transition-colors group"
      :class="selectedId === cat.id ? 'bg-blue-100 text-blue-700 font-bold' : 'text-zinc-600'"
      :style="{ paddingLeft: `${12 + depth * 16}px` }"
      @click="$emit('select', cat.id)"
    >
      <div class="flex items-center gap-1 min-w-0">
        <button
          v-if="cat.children?.length"
          @click.stop="$emit('toggle', cat.id)"
          class="text-zinc-400 hover:text-zinc-600 w-4 text-center shrink-0"
        >{{ expandedIds.has(cat.id) ? '▾' : '▸' }}</button>
        <span v-else class="w-4 shrink-0"></span>
        <span v-if="cat.is_system" title="系统预置" class="text-[10px] shrink-0">🔒</span>
        <span class="truncate">{{ cat.name }}</span>
        <span class="text-[10px] text-zinc-400 shrink-0">({{ cat.article_count }})</span>
      </div>
      <div class="hidden group-hover:flex items-center gap-0.5 shrink-0">
        <button v-if="!cat.is_system" @click.stop="$emit('edit', cat)" title="编辑" class="text-[10px] px-1 text-zinc-400 hover:text-blue-600">✎</button>
        <button @click.stop="$emit('add', cat.id)" title="添加子分类" class="text-[10px] px-1 text-zinc-400 hover:text-green-600">+</button>
        <button v-if="!cat.is_system" @click.stop="$emit('remove', cat)" title="删除" class="text-[10px] px-1 text-zinc-400 hover:text-red-500">×</button>
      </div>
    </div>
    <template v-if="cat.children?.length && expandedIds.has(cat.id)">
      <CategoryTreeNode
        v-for="child in cat.children"
        :key="child.id"
        :cat="child"
        :selected-id="selectedId"
        :expanded-ids="expandedIds"
        :depth="depth + 1"
        @select="$emit('select', $event)"
        @toggle="$emit('toggle', $event)"
        @add="$emit('add', $event)"
        @edit="$emit('edit', $event)"
        @remove="$emit('remove', $event)"
      />
    </template>
  </div>
</template>
```

- [ ] **Step 2: 在 KnowledgeBase.vue 中导入组件 + 追加分类管理对话框**

在 `<script setup>` 顶部追加 import：

```typescript
import CategoryTreeNode from '../components/kb/CategoryTreeNode.vue'
```

在 `</template>` 结束标签前（line 319 的 `</div>` 之后），追加分类管理对话框：

```vue

    <!-- Category Dialog -->
    <div v-if="catDialogVisible" class="fixed inset-0 bg-black/40 flex items-start justify-center z-50 pt-20">
      <div class="bg-white rounded-lg w-96">
        <div class="p-4 border-b flex items-center justify-between">
          <h3 class="font-bold text-sm">{{ catDialogMode === 'create' ? '新增子分类' : '编辑分类' }}</h3>
          <button @click="catDialogVisible = false" class="text-zinc-400 hover:text-zinc-600">&times;</button>
        </div>
        <div class="p-4 space-y-3">
          <div>
            <label class="text-xs text-zinc-500">父分类</label>
            <div class="text-sm text-zinc-700 mt-1">{{ findCatName(catForm.parent_id) || '根目录' }}</div>
          </div>
          <div>
            <label class="text-xs text-zinc-500">分类名称</label>
            <input v-model="catForm.name" @keydown.enter="saveCat" class="w-full border rounded px-2 py-1.5 text-sm mt-1" placeholder="输入分类名称" />
          </div>
        </div>
        <div class="p-4 border-t flex justify-end gap-2">
          <button @click="catDialogVisible = false" class="px-4 py-1.5 border rounded text-sm">取消</button>
          <button @click="saveCat" class="px-4 py-1.5 bg-blue-600 text-white rounded text-sm">保存</button>
        </div>
      </div>
    </div>
```

- [ ] **Step 3: 验证前端编译 + 浏览器功能**

```bash
cd frontend && npx vue-tsc --noEmit 2>&1 | grep -i error | head -10
```
Expected: 无新错误

浏览器验证：
1. 左侧树形分类正确展示 8 个 L1，默认展开
2. 点击 L1 展开/折叠 L2
3. hover 显示 +/✎/× 按钮
4. 点击 + 弹出新增对话框
5. L1 显示 🔒 图标，无编辑/删除按钮

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/kb/CategoryTreeNode.vue frontend/src/views/KnowledgeBase.vue
git commit -m "feat(kb): add CategoryTreeNode recursive component + category management dialog"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```


### Task 9: 端到端验证 + 数据迁移

**Files:**
- 无新文件（在步骤中执行迁移脚本）

- [ ] **Step 1: 迁移现有文章数据 —— 将旧 category 字符串映射到新 category_id**

在 Python shell 中执行一次性迁移：

```bash
cd backend && uv run python -c "
from app.database import SessionLocal, init_db, run_migrations
from app.models import KbArticle, KbCategory

init_db()
run_migrations()
db = SessionLocal()

# 建立旧分类名 → 新 category_id 的映射
# 旧分类: inbox/legal/finance/tax/wiki/resources/skills/agents/claude/gemini
# 新映射: inbox→inbox(通用), legal→法律合规, finance→财务会计, tax→税务政策(财务会计子类),
#          wiki→资源库(产品与项目), resources→AI研究, skills→Claude/Anthropic,
#          agents→其他AI工具, claude→Claude/Anthropic, gemini→Gemini/Google

mapping = {
    'legal': '法律合规',
    'finance': '财务会计',
    'tax': '会计准则',       # 税务相关放到财务会计 > 会计准则
    'wiki': '入职指南',      # 百科放到人力 > 入职指南
    'resources': '行业动态', # 资源库放到 AI研究 > 行业动态
    'skills': 'AI 安全与对齐', # 技能放到 AI研究 > AI安全
    'agents': '其他 AI 工具',
    'claude': 'Claude/Anthropic',
    'gemini': 'Gemini/Google',
    'inbox': '入职指南',     # inbox 暂放到入职指南
}

# 获取所有分类
all_cats = db.query(KbCategory).all()
name_to_id = {}
for c in all_cats:
    # 直接按名字匹配
    if c.name not in name_to_id:
        name_to_id[c.name] = c.id

count = 0
for article in db.query(KbArticle).all():
    if article.category and not article.category_id:
        cat_name = mapping.get(article.category)
        if cat_name and cat_name in name_to_id:
            article.category_id = name_to_id[cat_name]
            count += 1

db.commit()
print(f'Migrated {count} articles to new category_id')
db.close()
"
```

- [ ] **Step 2: 浏览器端到端验证**

Golden path:
1. 登录 → 知识库 → 左侧树形分类可见
2. 点击 "财务会计" → 中栏筛选该分类及其子类的文章
3. 点击 "新建文章" → 分类下拉显示 optgroup 层级
4. 编辑分类名称 → 保存成功
5. 新增子分类 → 保存成功，树自动刷新
6. 删除空分类 → 成功
7. 删除有文章的分类 → 报错提示
8. 尝试删除 L1 → 前端看不到删除按钮（后端 403）

Edge cases:
- 空分类树 → 显示"暂无分类"
- 无文章匹配 → 中栏显示"暂无文章"
- 分类名称空白 → 后端拒绝

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "feat(kb): end-to-end verification + legacy data migration"

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```
