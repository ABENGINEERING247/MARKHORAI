"""SQLAlchemy persistence; SQLite for local demo, PostgreSQL via DATABASE_URL for deployment."""
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, String, Text, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker, relationship

class Base(DeclarativeBase): pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    details: Mapped[str] = mapped_column(Text, default="")
    agent_id: Mapped[str] = mapped_column(String(10), default="001")
    due_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    status: Mapped[str] = mapped_column(String(30), default="scheduled", index=True)
    notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class Memory(Base):
    __tablename__ = "memories"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    agent_id: Mapped[str] = mapped_column(String(10), default="001")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

class PushSubscription(Base):
    __tablename__ = "push_subscriptions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    endpoint: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not DATABASE_URL:
    try:
        DATABASE_URL = str(__import__('streamlit').secrets.get("DATABASE_URL", "")).strip()
    except Exception:
        DATABASE_URL = ""
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+psycopg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///markhor_local.db"
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base.metadata.create_all(engine)

def session(): return SessionLocal()
