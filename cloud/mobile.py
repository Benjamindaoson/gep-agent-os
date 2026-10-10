"""Android opt-in activity ingestion with revocable, per-user device credentials."""
from __future__ import annotations
import hashlib,secrets
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException,Request
from pydantic import BaseModel,Field
from sqlalchemy import String,ForeignKey,DateTime,Integer,UniqueConstraint,select,delete
from sqlalchemy.orm import Mapped,mapped_column,Session
from .db import Base
from .models import uid,now,User
from .app import db_session,me

class MobileDevice(Base):
 __tablename__="mobile_devices"
 id:Mapped[str]=mapped_column(String(32),primary_key=True,default=uid)
 user_id:Mapped[str]=mapped_column(ForeignKey("users.id"),index=True)
 label:Mapped[str]=mapped_column(String(100))
 token_hash:Mapped[str]=mapped_column(String(64),unique=True,index=True)
 revoked:Mapped[bool]=mapped_column(default=False)
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
 last_seen_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True),nullable=True)
class MobileUsage(Base):
 __tablename__="mobile_usage"
 __table_args__=(UniqueConstraint("device_id","bucket_start_ms","package_name",name="uq_device_usage_bucket"),)
 id:Mapped[str]=mapped_column(String(32),primary_key=True,default=uid)
 user_id:Mapped[str]=mapped_column(ForeignKey("users.id"),index=True)
 device_id:Mapped[str]=mapped_column(ForeignKey("mobile_devices.id"),index=True)
 bucket_start_ms:Mapped[int]=mapped_column(Integer)
 bucket_end_ms:Mapped[int]=mapped_column(Integer)
 package_name:Mapped[str]=mapped_column(String(250))
 foreground_ms:Mapped[int]=mapped_column(Integer)
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)

class DeviceIn(BaseModel):
 label:str=Field(min_length=1,max_length=100)
class UsageEvent(BaseModel):
 start_ms:int=Field(ge=0)
 end_ms:int=Field(gt=0)
 package:str=Field(min_length=1,max_length=250,pattern=r"^[a-zA-Z0-9_.]+$")
 foreground_ms:int=Field(ge=0,le=86_400_000)
class Batch(BaseModel):
 events:list[UsageEvent]=Field(min_length=0,max_length=1000)

router=APIRouter(prefix="/api/mobile",tags=["mobile"])
def device_for_token(request:Request,db:Session)->MobileDevice:
 token=request.headers.get("Authorization","")
 if not token.startswith("Bearer "):raise HTTPException(401,"Device token required")
 secret=token[7:].strip()
 if not secret or len(secret)>256:raise HTTPException(401,"Invalid device token")
 digest=hashlib.sha256(secret.encode()).hexdigest()
 device=db.scalar(select(MobileDevice).where(MobileDevice.token_hash==digest,MobileDevice.revoked.is_(False)))
 if not device:raise HTTPException(401,"Device not registered or revoked")
 return device

@router.post("/devices")
def register_device(data:DeviceIn,user:User=Depends(me),db:Session=Depends(db_session)):
 raw="gep_android_"+secrets.token_urlsafe(32)
 device=MobileDevice(user_id=user.id,label=data.label,token_hash=hashlib.sha256(raw.encode()).hexdigest())
 db.add(device);db.commit()
 return {"id":device.id,"label":device.label,"token":raw,"note":"Token is displayed once. Save it on Android; never publish it."}

@router.get("/devices")
def list_devices(user:User=Depends(me),db:Session=Depends(db_session)):
 devices=db.scalars(select(MobileDevice).where(MobileDevice.user_id==user.id)).all()
 return [{"id":d.id,"label":d.label,"revoked":d.revoked,"last_seen_at":d.last_seen_at} for d in devices]

@router.delete("/devices/{device_id}")
def revoke_device(device_id:str,user:User=Depends(me),db:Session=Depends(db_session)):
 device=db.scalar(select(MobileDevice).where(MobileDevice.id==device_id,MobileDevice.user_id==user.id))
 if not device:raise HTTPException(404,"Device not found")
 device.revoked=True;db.commit()
 return {"revoked":True}

@router.post("/usage")
def ingest_usage(batch:Batch,request:Request,db:Session=Depends(db_session)):
 device=device_for_token(request,db)
 now_ms=int(datetime.now(timezone.utc).timestamp()*1000)
 accepted=0
 # Each batch contains one non-overlapping reporting window. Duplicates are ignored.
 for e in batch.events:
  duration=e.end_ms-e.start_ms
  if duration<=0 or duration>24*3600*1000 or e.foreground_ms>duration:
   raise HTTPException(422,"Invalid measurement interval")
  if e.end_ms>now_ms+300_000 or e.start_ms<now_ms-31*86400_000:
   raise HTTPException(422,"Outside allowed ingestion window")
  found=db.scalar(select(MobileUsage.id).where(
      MobileUsage.device_id==device.id,MobileUsage.bucket_start_ms==e.start_ms,
      MobileUsage.package_name==e.package))
  if found:continue
  db.add(MobileUsage(user_id=device.user_id,device_id=device.id,
     bucket_start_ms=e.start_ms,bucket_end_ms=e.end_ms,package_name=e.package,
     foreground_ms=e.foreground_ms))
  accepted+=1
 device.last_seen_at=now()
 db.commit()
 return {"accepted":accepted,"duplicate_or_empty":len(batch.events)-accepted}

@router.get("/usage")
def usage_summary(user:User=Depends(me),db:Session=Depends(db_session)):
 rows=db.scalars(select(MobileUsage).where(MobileUsage.user_id==user.id)
                .order_by(MobileUsage.bucket_start_ms.desc()).limit(5000)).all()
 summaries={}
 for r in rows:summaries[r.package_name]=summaries.get(r.package_name,0)+r.foreground_ms
 return {"source":"authorized_android_usage_stats","apps":[
  {"package":key,"minutes":round(ms/60000,1)}
  for key,ms in sorted(summaries.items(),key=lambda x:-x[1])],
  "note":"Aggregated usage evidence, not proof of productivity or goal achievement."}

@router.delete("/usage")
def delete_usage(user:User=Depends(me),db:Session=Depends(db_session)):
 db.execute(delete(MobileUsage).where(MobileUsage.user_id==user.id))
 db.commit()
 return {"deleted":True}
