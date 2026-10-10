"""Signed browser sessions and conservative deployment settings."""
import os,time
import jwt
from pwdlib import PasswordHash
from fastapi import Request,HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import User

HASH=PasswordHash.recommended()
COOKIE="gep_session"
SECRET=os.environ.get("GEP_SESSION_SECRET","")
if not SECRET and os.environ.get("GEP_ENV")=="production":
 raise RuntimeError("GEP_SESSION_SECRET is required in production")
if not SECRET:SECRET="dev-only-not-for-production-secret-change-me"
def issue(user_id):
 return jwt.encode({"sub":user_id,"exp":int(time.time())+7*86400},SECRET,algorithm="HS256")
def current(request:Request,db:Session):
 token=request.cookies.get(COOKIE)
 if not token:raise HTTPException(401,"Please sign in")
 try:
  payload=jwt.decode(token,SECRET,algorithms=["HS256"])
  user=db.get(User,payload["sub"])
  if user:return user
 except (jwt.PyJWTError,KeyError):pass
 raise HTTPException(401,"Session invalid or expired")
def guard_origin(request:Request):
 if request.method in ("POST","PATCH","PUT","DELETE"):
  origin=request.headers.get("origin")
  host=request.headers.get("host","")
  if origin:
   from urllib.parse import urlparse
   parsed=urlparse(origin)
   if parsed.netloc!=host or parsed.scheme not in ("http","https"):
    raise HTTPException(403,"Cross-origin mutation refused")
  elif request.headers.get("content-type","").split(";")[0].strip()!="application/json":
   raise HTTPException(403,"JSON request required")
