from __future__ import annotations

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .schemas import (
    ChatRequest, ChatResponse, HealthResponse,
    NoteMakerRequest, FlashcardGeneratorRequest, ConceptExplainerRequest,
)
from .db import (
    get_session_factory,
    get_or_create_user,
    create_chat_session,
    add_message,
    User,
    ChatSession,
    adjust_mastery,
)
from .orchestrator import build_graph, OrchestratorState

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse()


# Mock tool endpoints to simulate tool APIs
@router.post("/note_maker")
async def note_maker(req: NoteMakerRequest):
    return {"ok": True, "data": {"type": "notes", "summary": f"Notes for {req.subject}/{req.topic}", "detail_level": req.detail_level, "key_points": req.key_points}}


@router.post("/flashcard_generator")
async def flashcard_generator(req: FlashcardGeneratorRequest):
    return {"ok": True, "data": {"type": "flashcards", "count": req.num_cards, "style": req.style}}


@router.post("/concept_explainer")
async def concept_explainer(req: ConceptExplainerRequest):
    return {"ok": True, "data": {"type": "explanation", "concept": req.concept, "level": req.target_level}}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_factory = await get_session_factory()
    async with session_factory() as db:  # type: AsyncSession
        user = await get_or_create_user(db, req.user_id)
        chat_obj: ChatSession
        if req.chat_id is None:
            chat_obj = await create_chat_session(db, user, title=f"Chat with {user.id}")
        else:
            result = await db.execute(select(ChatSession).where(ChatSession.id == req.chat_id))
            chat_obj = result.scalar_one_or_none()
            if chat_obj is None:
                chat_obj = await create_chat_session(db, user, title=f"Chat with {user.id}")

        await add_message(db, chat_obj, role="user", content=req.message)

        graph = build_graph()
        state = OrchestratorState(message=req.message)
        out_state = await graph.ainvoke(state)

        # Persist assistant result summary
        result_preview = str(out_state.result)[:500]
        await add_message(db, chat_obj, role="assistant", content=result_preview)

        # Update mastery based on perceived difficulty and sentiment
        try:
            analysis = out_state.analysis or {}
            subject = analysis.get("subject", "general")
            difficulty = (analysis.get("difficulty") or "beginner").lower()
            sentiment = (analysis.get("sentiment") or "curious").lower()

            delta = 0.0
            if difficulty == "advanced":
                delta -= 0.02
            elif difficulty == "intermediate":
                delta -= 0.01
            else:
                delta += 0.01

            if sentiment == "confident":
                delta += 0.02
            elif sentiment == "frustrated":
                delta -= 0.02
            elif sentiment == "confused":
                delta -= 0.01

            await adjust_mastery(db, user, subject, delta)
        except Exception:
            # Soft-fail mastery adjustments
            pass
        await db.commit()

        return ChatResponse(
            chosen_tool=out_state.tool_choice.name if out_state.tool_choice else "",
            parameters=out_state.tool_choice.parameters if out_state.tool_choice else {},
            result=out_state.result or {},
            analysis=out_state.analysis,  # type: ignore
        )
