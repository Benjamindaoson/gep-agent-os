"""SQLAlchemy persistence; PostgreSQL in production, SQLite only for development."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase,sessionmaker
URL=os.getenv("DATABASE_URL","sqlite:///./gep_cloud_dev.sqlite3")
if URL.startswith("postgres://"): URL="postgresql+psycopg://"+URL[len("postgres://"):]
elif URL.startswith("postgresql://"): URL="postgresql+psycopg://"+URL[len("postgresql://"):]
connect_args={"check_same_thread":False} if URL.startswith("sqlite:") else {}
engine=create_engine(URL,pool_pre_ping=True,connect_args=connect_args)
Session=sessionmaker(bind=engine,expire_on_commit=False)
class Base(DeclarativeBase): pass
