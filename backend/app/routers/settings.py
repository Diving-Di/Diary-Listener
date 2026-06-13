from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..memory import get_or_create_settings
from ..models import User
from ..schemas import SettingsIn, SettingsOut
from ..security import get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/", response_model=SettingsOut)
def get_settings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SettingsOut:
    settings = get_or_create_settings(db, user)
    return SettingsOut(allow_ai_diary=settings.allow_ai_diary)


@router.put("/", response_model=SettingsOut)
def update_settings(
    payload: SettingsIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SettingsOut:
    settings = get_or_create_settings(db, user)
    settings.allow_ai_diary = payload.allow_ai_diary
    db.commit()
    db.refresh(settings)
    return SettingsOut(allow_ai_diary=settings.allow_ai_diary)
