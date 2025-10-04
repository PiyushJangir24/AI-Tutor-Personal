from __future__ import annotations
import os
from typing import Dict, Any

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
import httpx

from db import lifespan, get_session
from sqlalchemy.ext.asyncio import AsyncSession
from schemas import OrchestrationRequest, OrchestrationResponse
from orchestrator import analyze_message, extract_params, validate_and_route, run_pipeline
from models import User, ChatMessage, Mastery

app = FastAPI(title="Autonomous AI Tutor Orchestrator", default_response_class=ORJSONResponse, lifespan=lifespan)

origins = (os.getenv("ALLOW_ORIGINS") or "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include mock tools
from tools.mock_tools import router as tools_router  # noqa: E402
app.include_router(tools_router)


async def _get_or_create_user(session: AsyncSession, external_id: str) -> User:
    from sqlalchemy import select
    res = await session.execute(select(User).where(User.external_id == external_id))
    user = res.scalars().first()
    if user is None:
        user = User(external_id=external_id)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


@app.post("/orchestrate", response_model=OrchestrationResponse)
async def orchestrate(req: OrchestrationRequest, session: AsyncSession = Depends(get_session)):
    user_id = req.user_id or "demo_user"
    user = await _get_or_create_user(session, user_id)

    pipeline = await run_pipeline(req.message)
    analysis = pipeline["analysis"]
    path = pipeline["route_path"]
    payload = pipeline["payload"]

    # Persist user message
    session.add(ChatMessage(user_id=user.id, role="user", content=req.message, tool_used=None, params=None))

    # Call result already produced by graph
    result = pipeline["result"]

    # Record assistant message
    session.add(ChatMessage(user_id=user.id, role="assistant", content=str(result), tool_used=analysis.intent, params=payload))
    # Update mastery (toy heuristic)
    from sqlalchemy import select
    res = await session.execute(select(Mastery).where(Mastery.user_id == user.id, Mastery.subject == analysis.subject))
    mastery = res.scalars().first()
    if mastery is None:
        mastery = Mastery(user_id=user.id, subject=analysis.subject, level=0.1)
        session.add(mastery)
    else:
        mastery.level = min(1.0, (mastery.level or 0) + 0.05)

    await session.commit()

    return OrchestrationResponse(
        user_id=user.external_id,
        chosen_tool=analysis.intent,
        extracted_parameters=payload,
        result=result,
        analysis=analysis,
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return ORJSONResponse(status_code=500, content={"error": "internal_error", "message": str(exc)})
