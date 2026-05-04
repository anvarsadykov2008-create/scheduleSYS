import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.models import AuditLog, User, UserRole
from app.dependencies import require_admin
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audit", tags=["Аудит"])

# Schema for response
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int]
    username: Optional[str]
    action: str
    entity: str
    entity_id: Optional[int]
    details: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("", response_model=List[AuditLogResponse])
def get_audit_logs(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    entity: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):


    query = db.query(AuditLog)
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity:
        query = query.filter(AuditLog.entity == entity)
        
    # Join with User to get username (though we just return user_id, frontend can fetch user or we can enrich)
    # Actually, let's just return the log. The Pydantic model can flatten if we want, but for now robust simple return.
    
    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()

    # Collect user_ids and fetch in one query to avoid N+1
    user_ids = {log.user_id for log in logs if log.user_id is not None}
    user_map: dict[int, str] = {}
    if user_ids:
        users = db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()
        user_map = {u.id: u.username for u in users}

    result = []
    for log in logs:
        username = user_map.get(log.user_id, "System/Deleted") if log.user_id else "System/Deleted"
        result.append(AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            username=username,
            action=log.action,
            entity=log.entity,
            entity_id=log.entity_id,
            details=log.details,
            created_at=log.created_at
        ))
        
    return result

def log_action(db: Session, user_id: Optional[int], action: str, entity: str, entity_id: Optional[int] = None, details: Optional[dict] = None):
    """Helper to create an audit log entry."""
    try:
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity=entity,
            entity_id=entity_id,
            details=details
        )
        db.add(log)
        db.commit()
    except Exception as e:
        logger.error("Failed to write audit log: %s", e)
