from __future__ import annotations

import asyncio
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Integer, Text, Float, func
from sqlalchemy.sql import select

from .config import settings


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[str] = mapped_column(String(32), server_default=func.now())

    chats: Mapped[list[ChatSession]] = relationship(back_populates="user", cascade="all, delete-orphan")
    mastery: Mapped[list[Mastery]] = relationship(back_populates="user", cascade="all, delete-orphan")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[str] = mapped_column(String(32), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="chats")
    messages: Mapped[list[Message]] = relationship(back_populates="chat", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id"))
    role: Mapped[str] = mapped_column(String(16))  # user|assistant|system
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String(32), server_default=func.now())

    chat: Mapped[ChatSession] = relationship(back_populates="messages")


class Mastery(Base):
    __tablename__ = "mastery"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    subject: Mapped[str] = mapped_column(String(128))
    level: Mapped[float] = mapped_column(Float, default=0.5)  # 0-1 scale

    user: Mapped[User] = relationship(back_populates="mastery")


async def _try_create_engine(db_url: str) -> AsyncEngine | None:
    try:
        engine = create_async_engine(db_url, echo=False, pool_pre_ping=True)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return engine
    except Exception:
        return None


async def create_engine_with_fallback() -> AsyncEngine:
    # First try Postgres from .env, then fallback to SQLite file
    pg_url = settings.database_url
    engine = await _try_create_engine(pg_url)
    if engine is not None:
        return engine
    sqlite_url = "sqlite+aiosqlite:///./ai_tutor.db"
    engine = await _try_create_engine(sqlite_url)
    if engine is None:
        raise RuntimeError("Failed to initialize any database engine")
    return engine


async def get_session_factory() -> async_sessionmaker[AsyncSession]:
    engine = await create_engine_with_fallback()
    return async_sessionmaker(engine, expire_on_commit=False)


# Simple helpers used by routes
async def get_or_create_user(session: AsyncSession, user_id: int | None) -> User:
    if user_id is not None:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            return user
    user = User(name=None)
    session.add(user)
    await session.flush()
    return user


async def create_chat_session(session: AsyncSession, user: User, title: str | None = None) -> ChatSession:
    chat = ChatSession(user_id=user.id, title=title)
    session.add(chat)
    await session.flush()
    return chat


async def add_message(session: AsyncSession, chat: ChatSession, role: str, content: str) -> Message:
    message = Message(chat_id=chat.id, role=role, content=content)
    session.add(message)
    await session.flush()
    return message


async def get_or_create_mastery(session: AsyncSession, user: User, subject: str) -> Mastery:
    result = await session.execute(
        select(Mastery).where(Mastery.user_id == user.id, Mastery.subject == subject)
    )
    mastery = result.scalar_one_or_none()
    if mastery is not None:
        return mastery
    mastery = Mastery(user_id=user.id, subject=subject, level=0.5)
    session.add(mastery)
    await session.flush()
    return mastery


async def adjust_mastery(session: AsyncSession, user: User, subject: str, delta: float) -> Mastery:
    mastery = await get_or_create_mastery(session, user, subject)
    current = mastery.level if mastery.level is not None else 0.5
    new_level = max(0.0, min(1.0, current + delta))
    mastery.level = new_level
    await session.flush()
    return mastery
