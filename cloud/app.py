"""Hosted GEP web app — individual account data, cross-device state, and human approvals."""
import os
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import FastAPI,Depends,HTTPException,Request,Response
from fastapi.responses import HTMLResponse,FileResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel,Field
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from .db import Base,engine,Session as DB
from .models import User,Goal,Project,Task,Mission,MissionEvent
from .security import HASH,COOKIE,issue,current,guard_origin

@asynccontextmanager
async def lifecycle(app):
 Base.metadata.create_all(engine)
 yield
app=FastAPI(title="GEP Cloud",version="0.2.0",lifespan=lifecycle)
app.add_middleware(TrustedHostMiddleware,allowed_hosts=os.environ.get("GEP_ALLOWED_HOSTS","localhost,127.0.0.1,testserver").split(","))
def db_session():
 with DB() as db:yield db
def me(request:Request,db:Session=Depends(db_session)):
 return current(request,db)
@app.middleware("http")
async def origin_policy(request,call_next):
 if request.url.path.startswith("/api/"):
  guard_origin(request)
 return await call_next(request)
def own(db,model,id,user):
 row=db.scalar(select(model).where(model.id==id,model.user_id==user.id))
 if not row:raise HTTPException(404,"Not found")
 return row
def emit(db,user,mission,event,detail=""):
 db.add(MissionEvent(user_id=user.id,mission_id=mission.id,event=event,detail=detail))
def dto(x,fields):
 return {field:getattr(x,field) for field in fields}
class Credentials(BaseModel):
 email:str=Field(min_length=5,max_length=320)
 password:str=Field(min_length=12,max_length=256)
class GoalIn(BaseModel):
 name:str=Field(min_length=1,max_length=200)
 domain:str="career"
 horizon:str="quarter"
 priority:int=Field(default=3,ge=1,le=5)
 protected:bool=False
class ProjectIn(BaseModel):
 name:str=Field(min_length=1,max_length=200)
 goal_id:str
class TaskIn(BaseModel):
 title:str=Field(min_length=1,max_length=250)
 project_id:str
class EvidenceIn(BaseModel):
 uri:str=Field(min_length=1,max_length=1000)
class MissionIn(BaseModel):
 goal_id:str
 instruction:str=Field(min_length=4,max_length=10000)
class Change(BaseModel):
 state:str
class Review(BaseModel):
 note:str=Field(max_length=1000,default="")

@app.get("/health")
def health():return {"ok":True,"service":"gep-cloud"}
@app.get("/",response_class=HTMLResponse)
def index():
 return (Path(__file__).parent/"static"/"index.html").read_text(encoding="utf-8")
@app.post("/api/register")
def register(data:Credentials,response:Response,db:Session=Depends(db_session)):
 email=data.email.strip().lower()
 if "@" not in email:raise HTTPException(422,"Valid email required")
 if db.scalar(select(User).where(User.email==email)):raise HTTPException(409,"Account exists")
 user=User(email=email,password_hash=HASH.hash(data.password));db.add(user);db.commit();db.refresh(user)
 response.set_cookie(COOKIE,issue(user.id),httponly=True,secure=os.getenv("GEP_ENV")=="production",samesite="strict",max_age=604800)
 return {"id":user.id,"email":user.email}
@app.post("/api/login")
def login(data:Credentials,response:Response,db:Session=Depends(db_session)):
 user=db.scalar(select(User).where(User.email==data.email.strip().lower()))
 if not user or not HASH.verify(data.password,user.password_hash):raise HTTPException(401,"Wrong credentials")
 response.set_cookie(COOKIE,issue(user.id),httponly=True,secure=os.getenv("GEP_ENV")=="production",samesite="strict",max_age=604800)
 return {"id":user.id,"email":user.email}
@app.post("/api/logout")
def logout(response:Response):
 response.delete_cookie(COOKIE);return {"ok":True}
@app.get("/api/me")
def profile(user:User=Depends(me)):return {"id":user.id,"email":user.email}

@app.get("/api/state")
def state(user:User=Depends(me),db:Session=Depends(db_session)):
 goals=db.scalars(select(Goal).where(Goal.user_id==user.id).order_by(Goal.created_at)).all()
 projects=db.scalars(select(Project).where(Project.user_id==user.id).order_by(Project.created_at)).all()
 tasks=db.scalars(select(Task).where(Task.user_id==user.id).order_by(Task.created_at)).all()
 missions=db.scalars(select(Mission).where(Mission.user_id==user.id).order_by(Mission.created_at)).all()
 events=db.scalars(select(MissionEvent).where(MissionEvent.user_id==user.id).order_by(MissionEvent.at.desc()).limit(100)).all()
 return {
 "goals":[dto(x,["id","name","domain","horizon","priority","protected"]) for x in goals],
 "projects":[dto(x,["id","goal_id","name","status"]) for x in projects],
 "tasks":[dto(x,["id","project_id","title","state","evidence_uri"]) for x in tasks],
 "missions":[dto(x,["id","goal_id","instruction","state","progress","approval"]) for x in missions],
 "events":[dto(x,["mission_id","event","detail"]) for x in events]}
@app.post("/api/goals")
def add_goal(data:GoalIn,user:User=Depends(me),db:Session=Depends(db_session)):
 if data.domain not in ("career","learning","life","health","finance","exploration"):raise HTTPException(422,"Invalid domain")
 goal=Goal(user_id=user.id,**data.model_dump());db.add(goal);db.commit()
 return {"id":goal.id}
@app.post("/api/projects")
def add_project(data:ProjectIn,user:User=Depends(me),db:Session=Depends(db_session)):
 own(db,Goal,data.goal_id,user)
 p=Project(user_id=user.id,**data.model_dump());db.add(p);db.commit();return {"id":p.id}
@app.patch("/api/projects/{id}")
def update_project(id:str,data:Change,user:User=Depends(me),db:Session=Depends(db_session)):
 p=own(db,Project,id,user)
 if data.state not in ("proposed","active","paused","shipped"):raise HTTPException(422,"Invalid state")
 if data.state=="active" and p.status!="active":
  count=db.scalar(select(func.count()).select_from(Project).where(Project.user_id==user.id,Project.status=="active"))
  if count>=2:raise HTTPException(409,"Finish or pause an active project first (WIP limit: 2)")
 if data.state=="shipped":
  tasks=db.scalars(select(Task).where(Task.project_id==id,Task.user_id==user.id)).all()
  if not tasks or any(t.state!="verified" for t in tasks):raise HTTPException(409,"All tasks need accepted evidence before shipping")
 p.status=data.state;db.commit();return {"state":p.status}
@app.post("/api/tasks")
def add_task(data:TaskIn,user:User=Depends(me),db:Session=Depends(db_session)):
 own(db,Project,data.project_id,user)
 t=Task(user_id=user.id,**data.model_dump());db.add(t);db.commit();return {"id":t.id}
@app.post("/api/tasks/{id}/evidence")
def set_evidence(id:str,data:EvidenceIn,user:User=Depends(me),db:Session=Depends(db_session)):
 t=own(db,Task,id,user)
 t.evidence_uri=data.uri;t.state="awaiting_review";db.commit();return {"state":t.state}
@app.post("/api/tasks/{id}/accept")
def accept_task(id:str,user:User=Depends(me),db:Session=Depends(db_session)):
 t=own(db,Task,id,user)
 if t.state!="awaiting_review" or not t.evidence_uri:raise HTTPException(409,"Evidence required")
 t.state="verified";db.commit();return {"state":t.state}
@app.post("/api/missions")
def add_mission(data:MissionIn,user:User=Depends(me),db:Session=Depends(db_session)):
 own(db,Goal,data.goal_id,user)
 m=Mission(user_id=user.id,**data.model_dump());db.add(m);emit(db,user,m,"created");db.commit()
 return {"id":m.id,"state":m.state}
@app.post("/api/missions/{id}/approve")
def approve_mission(id:str,user:User=Depends(me),db:Session=Depends(db_session)):
 m=own(db,Mission,id,user)
 if m.state!="planned":raise HTTPException(409,"Mission no longer planned")
 m.approval=True;m.state="approved";emit(db,user,m,"approved");db.commit()
 return {"state":m.state}
@app.post("/api/missions/{id}/pause")
def pause_mission(id:str,user:User=Depends(me),db:Session=Depends(db_session)):
 m=own(db,Mission,id,user)
 if m.state not in ("approved","running"):raise HTTPException(409,"Cannot pause mission")
 m.state="paused";emit(db,user,m,"paused");db.commit();return {"state":m.state}
@app.post("/api/missions/{id}/resume")
def resume_mission(id:str,user:User=Depends(me),db:Session=Depends(db_session)):
 m=own(db,Mission,id,user)
 if m.state!="paused":raise HTTPException(409,"Not paused")
 m.state="approved";emit(db,user,m,"resumed");db.commit();return {"state":m.state}
@app.post("/api/missions/{id}/note")
def mission_note(id:str,data:Review,user:User=Depends(me),db:Session=Depends(db_session)):
 m=own(db,Mission,id,user)
 m.progress=data.note;emit(db,user,m,"progress_note",data.note);db.commit();return {"ok":True}
