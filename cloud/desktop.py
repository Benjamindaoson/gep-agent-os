"""Opt-in Windows activity and Git metadata ingestion.

A desktop token can only submit to its owning account. Browser sessions are
required for pairing, listing and deleting observations.
"""
from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import ForeignKey, String, Integer, BigInteger, UniqueConstraint, select, delete
from sqlalchemy.orm import Mapped, mapped_column, Session
from .db import Base
from .models import uid, now, User
from .app import db_session, me
from .mobile import MobileDevice, device_for_token

class DesktopObservation(Base):
    __tablename__ = "desktop_observations"
    __table_args__ = (UniqueConstraint("device_id", "period_start_ms", "kind", "identifier",
                                       name="uq_desktop_device_window_kind_identifier"),)
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("mobile_devices.id"), index=True)
    period_start_ms: Mapped[int] = mapped_column(BigInteger)
    period_end_ms: Mapped[int] = mapped_column(BigInteger)
    kind: Mapped[str] = mapped_column(String(24))
    identifier: Mapped[str] = mapped_column(String(180))
    seconds: Mapped[int] = mapped_column(Integer, default=0)
    detail: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(default=now)

class DesktopEvent(BaseModel):
    start_ms: int = Field(ge=0)
    end_ms: int = Field(gt=0)
    kind: str = Field(pattern="^(app|git)$")
    identifier: str = Field(min_length=1, max_length=180)
    seconds: int = Field(ge=0, le=86400)
    detail: str = Field(default="", max_length=200)

class DesktopBatch(BaseModel):
    events: list[DesktopEvent] = Field(max_length=500)

router = APIRouter(prefix="/api/desktop", tags=["desktop"])

@router.post("/events")
def ingest(batch: DesktopBatch, request: Request, db: Session = Depends(db_session)):
    device = device_for_token(request, db)
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    validated = []
    for event in batch.events:
        span = event.end_ms - event.start_ms
        if span <= 0 or span > 24 * 3600 * 1000 or event.seconds * 1000 > span:
            raise HTTPException(422, "Invalid activity time window")
        if event.end_ms > now_ms + 300000 or event.start_ms < now_ms - 31 * 86400 * 1000:
            raise HTTPException(422, "Activity outside allowed history")
        validated.append(event)
    accepted = 0
    for item in validated:
        found = db.scalar(select(DesktopObservation.id).where(
            DesktopObservation.device_id == device.id,
            DesktopObservation.period_start_ms == item.start_ms,
            DesktopObservation.kind == item.kind,
            DesktopObservation.identifier == item.identifier))
        if found:
            continue
        db.add(DesktopObservation(user_id=device.user_id, device_id=device.id,
            period_start_ms=item.start_ms, period_end_ms=item.end_ms, kind=item.kind,
            identifier=item.identifier, seconds=item.seconds, detail=item.detail))
        accepted += 1
    device.last_seen_at = now()
    db.commit()
    return {"accepted": accepted, "duplicates": len(validated) - accepted}

@router.get("/summary")
def summary(user: User = Depends(me), db: Session = Depends(db_session)):
    records = db.scalars(select(DesktopObservation)
        .where(DesktopObservation.user_id == user.id)
        .order_by(DesktopObservation.period_start_ms.desc()).limit(5000)).all()
    grouped: dict[str, dict] = {}
    git = []
    for r in records:
        if r.kind == "app":
            item = grouped.setdefault(r.identifier, {"app": r.identifier, "seconds": 0})
            item["seconds"] += r.seconds
        else:
            git.append({"project": r.identifier, "state": r.detail, "at": r.period_start_ms})
    return {"apps": sorted(grouped.values(), key=lambda x: -x["seconds"]),
            "git": git[:50],
            "note": "Observed application time is not verified productivity or progress."}

@router.delete("/events")
def clear(user: User = Depends(me), db: Session = Depends(db_session)):
    db.execute(delete(DesktopObservation).where(DesktopObservation.user_id == user.id))
    db.commit()
    return {"deleted": True}
