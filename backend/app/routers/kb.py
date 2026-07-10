"""知识库管理 — 文章 CRUD + 分类检索 + 审计 + 批量 + 导出."""

import csv as csv_mod
import io
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import get_current_user
from app.models import KbArticle, KbCategory, AuditLog, User
from app.schemas import KbArticleCreate, KbArticleUpdate, KbCategoryCreate, KbCategoryUpdate, KbCategoryResponse
from sqlalchemy import func

router = APIRouter()


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
        "id": item.id,
        "company_id": item.company_id,
        "title": item.title,
        "content_md": item.content_md,
        "category_id": item.category_id,
        "category_name": cat_map.get(item.category_id) if item.category_id else None,
        "tags": item.tags,
        "author": item.author,
        "status": item.status,
        "version": item.version,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


def _audit(
    db: Session,
    user: User,
    action: str,
    target_id: int | None = None,
    details: dict | None = None,
    target_type: str = "kb_article",
):
    db.add(
        AuditLog(
            company_id=getattr(user, "company_id", 1),
            user_id=user.id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
            created_at=datetime.utcnow(),
        )
    )


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
        all_cats = db.query(KbCategory).filter(KbCategory.company_id == company_id, KbCategory.is_active).all()
        ids = _get_descendant_ids(all_cats, category_id)
        q = q.filter(KbArticle.category_id.in_(ids))
    if status:
        q = q.filter(KbArticle.status == status)
    if search:
        pattern = f"%{search}%"
        q = q.filter((KbArticle.title.ilike(pattern)) | (KbArticle.content_md.ilike(pattern)))
    items = q.order_by(KbArticle.updated_at.desc()).offset(offset).limit(limit).all()
    cat_ids = {i.category_id for i in items if i.category_id}
    cat_map = {}
    if cat_ids:
        cat_map = {c.id: c.name for c in db.query(KbCategory).filter(KbCategory.id.in_(cat_ids)).all()}
    return [_article_dict(item, cat_map) for item in items]


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
        writer.writerow(
            [
                i.title,
                cat_name,
                i.author or "",
                i.status,
                i.version,
                i.tags or "",
                (i.updated_at.strftime("%Y-%m-%d %H:%M") if i.updated_at else ""),
                (i.content_md or "")[:500],
            ]
        )
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=kb_articles.csv"},
    )


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


@router.post("/articles")
def create_article(data: KbArticleCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not data.title.strip():
        raise HTTPException(status_code=400, detail="标题不能为空")
    cat = (
        db.query(KbCategory).filter(KbCategory.id == data.category_id, KbCategory.company_id == data.company_id).first()
    )
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


@router.put("/articles/{article_id}")
def update_article(
    article_id: int, data: KbArticleUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    item = db.query(KbArticle).filter(KbArticle.id == article_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="文章不存在")
    update_data = data.model_dump(exclude_unset=True, exclude={"tags"})
    if "category_id" in update_data:
        cat = (
            db.query(KbCategory)
            .filter(KbCategory.id == update_data["category_id"], KbCategory.company_id == item.company_id)
            .first()
        )
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


@router.delete("/articles/{article_id}")
def delete_article(article_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(KbArticle).filter(KbArticle.id == article_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="文章不存在")
    _audit(db, user, "delete", item.id, {"title": item.title})
    db.delete(item)
    db.commit()
    return {"ok": True}


class BatchDeleteRequest(BaseModel):
    ids: list[int]


@router.post("/articles/batch-delete")
def batch_delete_articles(
    data: BatchDeleteRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    count = db.query(KbArticle).filter(KbArticle.id.in_(data.ids)).delete(synchronize_session=False)
    _audit(db, user, "batch_delete", None, {"deleted_count": count, "ids": data.ids})
    db.commit()
    return {"deleted": count}


# ═══════════ 分类管理 ═══════════


def _build_tree(categories: list, article_counts: dict, parent_id: int | None = None) -> list[dict]:
    result = []
    for cat in categories:
        if cat.parent_id == parent_id:
            result.append(
                {
                    "id": cat.id,
                    "name": cat.name,
                    "level": cat.level,
                    "is_system": cat.is_system,
                    "sort_order": cat.sort_order,
                    "article_count": article_counts.get(cat.id, 0),
                    "children": _build_tree(categories, article_counts, cat.id),
                }
            )
    result.sort(key=lambda x: (x["sort_order"], x["id"]))
    return result


@router.get("/categories")
def list_categories(
    company_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cats = (
        db.query(KbCategory)
        .filter(
            KbCategory.company_id == company_id,
            KbCategory.is_active,
        )
        .order_by(KbCategory.sort_order, KbCategory.id)
        .all()
    )

    article_counts = dict(
        db.query(KbArticle.category_id, func.count(KbArticle.id))
        .filter(KbArticle.company_id == company_id, KbArticle.category_id.in_([c.id for c in cats]))
        .group_by(KbArticle.category_id)
        .all()
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
    if parent.company_id != data.company_id:
        raise HTTPException(status_code=403, detail="父分类不属于该公司")
    if not data.name.strip():
        raise HTTPException(status_code=400, detail="分类名称不能为空")
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
    _audit(
        db,
        user,
        "create_category",
        target_id=cat.id,
        details={"name": cat.name, "parent_id": data.parent_id},
        target_type="kb_category",
    )
    db.commit()
    return cat


@router.put("/categories/{cat_id}", response_model=KbCategoryResponse)
def update_category(
    cat_id: int,
    company_id: int,
    data: KbCategoryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cat = db.query(KbCategory).filter(KbCategory.id == cat_id, KbCategory.company_id == company_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    if cat.is_system and (user.role not in ("super_admin",) and not user.is_admin):
        raise HTTPException(status_code=403, detail="系统预置分类不可编辑")
    if data.name is not None:
        if not data.name.strip():
            raise HTTPException(status_code=400, detail="分类名称不能为空")
        cat.name = data.name.strip()
    if data.sort_order is not None:
        cat.sort_order = data.sort_order
    _audit(db, user, "update_category", target_id=cat.id, details={"name": cat.name}, target_type="kb_category")
    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/categories/{cat_id}")
def delete_category(
    cat_id: int,
    company_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cat = db.query(KbCategory).filter(KbCategory.id == cat_id, KbCategory.company_id == company_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    if cat.is_system:
        raise HTTPException(status_code=403, detail="系统预置分类不可删除")

    children = db.query(KbCategory).filter(KbCategory.parent_id == cat_id, KbCategory.company_id == company_id).count()
    if children > 0:
        raise HTTPException(status_code=400, detail="该分类下还有子分类，请先删除子分类")

    article_count = (
        db.query(KbArticle).filter(KbArticle.category_id == cat_id, KbArticle.company_id == company_id).count()
    )
    if article_count > 0:
        raise HTTPException(status_code=400, detail=f"该分类下有 {article_count} 篇文章，请先迁移或删除文章")

    can_delete = (
        user.is_admin
        or user.role in ("super_admin", "finance_director", "finance_manager")
        or cat.created_by == user.id
    )
    if not can_delete:
        raise HTTPException(status_code=403, detail="需上级批准：只有部门负责人或创建人可以删除分类")

    _audit(db, user, "delete_category", target_id=cat.id, details={"name": cat.name}, target_type="kb_category")
    db.delete(cat)
    db.commit()
    return {"ok": True}
