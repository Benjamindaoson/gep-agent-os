from datetime import datetime,timezone
from uuid import uuid4
from sqlalchemy import String,Text,DateTime,ForeignKey,Integer,Boolean,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column,relationship
from .db import Base

def uid():return uuid4().hex
def now():return datetime.now(timezone.utc)

class User(Base):
 __tablename__="users"
 id:Mapped[str]=mapped_column(String(32),primary_key=True,default=uid)
 email:Mapped[str]=mapped_column(String(320),unique=True,index=True)
 password_hash:Mapped[str]=mapped_column(Text)
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class Goal(Base):
 __tablename__="goals"
 id:Mapped[str]=mapped_column(String(32),primary_key=True,default=uid)
 user_id:Mapped[str]=mapped_column(ForeignKey("users.id"),index=True)
 name:Mapped[str]=mapped_column(String(200))
 domain:Mapped[str]=mapped_column(String(40),default="career")
 horizon:Mapped[str]=mapped_column(String(30),default="quarter")
 priority:Mapped[int]=mapped_column(Integer,default=3)
 protected:Mapped[bool]=mapped_column(Boolean,default=False)
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class Project(Base):
 __tablename__="projects"
 id:Mapped[str]=mapped_column(String(32),primary_key=True,default=uid)
 user_id:Mapped[str]=mapped_column(ForeignKey("users.id"),index=True)
 goal_id:Mapped[str]=mapped_column(ForeignKey("goals.id"),index=True)
 name:Mapped[str]=mapped_column(String(200))
 status:Mapped[str]=mapped_column(String(30),default="proposed")
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class Task(Base):
 __tablename__="tasks"
 id:Mapped[str]=mapped_column(String(32),primary_key=True,default=uid)
 user_id:Mapped[str]=mapped_column(ForeignKey("users.id"),index=True)
 project_id:Mapped[str]=mapped_column(ForeignKey("projects.id"),index=True)
 title:Mapped[str]=mapped_column(String(250))
 state:Mapped[str]=mapped_column(String(30),default="pending")
 evidence_uri:Mapped[str|None]=mapped_column(Text,nullable=True)
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class Mission(Base):
 __tablename__="missions"
 id:Mapped[str]=mapped_column(String(32),primary_key=True,default=uid)
 user_id:Mapped[str]=mapped_column(ForeignKey("users.id"),index=True)
 goal_id:Mapped[str]=mapped_column(ForeignKey("goals.id"),index=True)
 instruction:Mapped[str]=mapped_column(Text)
 state:Mapped[str]=mapped_column(String(30),default="planned")
 progress:Mapped[str]=mapped_column(Text,default="")
 approval:Mapped[bool]=mapped_column(Boolean,default=False)
 created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
 updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now,onupdate=now)
class MissionEvent(Base):
 __tablename__="mission_events"
 id:Mapped[str]=mapped_column(String(32),primary_key=True,default=uid)
 user_id:Mapped[str]=mapped_column(ForeignKey("users.id"),index=True)
 mission_id:Mapped[str]=mapped_column(ForeignKey("missions.id"),index=True)
 event:Mapped[str]=mapped_column(String(60))
 detail:Mapped[str]=mapped_column(Text,default="")
 at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
