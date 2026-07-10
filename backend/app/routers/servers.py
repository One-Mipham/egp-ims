"""服务器与服务管理路由。"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Server, ServerService
from app.schemas import (
    ServerCreate,
    ServerUpdate,
    ServerResponse,
    ServerServiceCreate,
    ServerServiceUpdate,
    ServerServiceResponse,
    ServerServiceStatusUpdate,
)
from app.auth import get_current_user

router = APIRouter()

# ═══════════ 服务器 CRUD ═══════════


@router.get("/", response_model=list[ServerResponse])
def list_servers(company_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Server).filter(Server.company_id == company_id).order_by(Server.name).all()


@router.post("/", response_model=ServerResponse)
def create_server(data: ServerCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    srv = Server(**data.model_dump())
    db.add(srv)
    db.commit()
    db.refresh(srv)
    return srv


@router.put("/{server_id}", response_model=ServerResponse)
def update_server(server_id: int, data: ServerUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    srv = db.query(Server).filter(Server.id == server_id).first()
    if not srv:
        raise HTTPException(status_code=404, detail="服务器不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(srv, k, v)
    srv.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(srv)
    return srv


@router.delete("/{server_id}")
def delete_server(server_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    srv = db.query(Server).filter(Server.id == server_id).first()
    if not srv:
        raise HTTPException(status_code=404, detail="服务器不存在")
    db.delete(srv)
    db.commit()
    return {"ok": True}


@router.get("/{server_id}", response_model=ServerResponse)
def get_server(server_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    srv = db.query(Server).filter(Server.id == server_id).first()
    if not srv:
        raise HTTPException(status_code=404, detail="服务器不存在")
    return srv


# ═══════════ 服务管理 CRUD ═══════════


@router.get("/{server_id}/services", response_model=list[ServerServiceResponse])
def list_services(server_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(ServerService).filter(ServerService.server_id == server_id).order_by(ServerService.name).all()


@router.post("/{server_id}/services", response_model=ServerServiceResponse)
def create_service(
    server_id: int, data: ServerServiceCreate, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    svc = ServerService(server_id=server_id, **data.model_dump(exclude={"server_id"}))
    db.add(svc)
    db.commit()
    db.refresh(svc)
    return svc


@router.put("/services/{service_id}", response_model=ServerServiceResponse)
def update_service(
    service_id: int, data: ServerServiceUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    svc = db.query(ServerService).filter(ServerService.id == service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail="服务不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(svc, k, v)
    svc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(svc)
    return svc


@router.delete("/services/{service_id}")
def delete_service(service_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    svc = db.query(ServerService).filter(ServerService.id == service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail="服务不存在")
    db.delete(svc)
    db.commit()
    return {"ok": True}


# ═══════════ 服务控制（启动/停止/重启） ═══════════


@router.post("/services/{service_id}/control", response_model=ServerServiceResponse)
def control_service(
    service_id: int, data: ServerServiceStatusUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    svc = db.query(ServerService).filter(ServerService.id == service_id).first()
    if not svc:
        raise HTTPException(status_code=404, detail="服务不存在")

    action = data.action
    if action == "start":
        svc.status = "running"
        svc.last_started_at = datetime.utcnow()
        svc.uptime_hours = 0
    elif action == "stop":
        svc.status = "stopped"
    elif action == "restart":
        svc.status = "running"
        svc.last_started_at = datetime.utcnow()
        svc.uptime_hours = 0
    else:
        raise HTTPException(status_code=400, detail=f"不支持的操作: {action}")

    svc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(svc)
    return svc


# ═══════════ 跨服务器：全部服务列表 ═══════════


@router.get("/all/services", response_model=list[ServerServiceResponse])
def list_all_services(company_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """列出当前公司所有服务器下的所有服务（按服务名排列）。"""
    return (
        db.query(ServerService)
        .join(Server, ServerService.server_id == Server.id)
        .filter(Server.company_id == company_id)
        .order_by(ServerService.name)
        .all()
    )
