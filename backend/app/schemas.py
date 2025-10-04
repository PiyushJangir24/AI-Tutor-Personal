from __future__ import annotations

from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Context Analysis
class ContextAnalysis(BaseModel):
    subject: str
    topic: str
    difficulty: Literal["beginner", "intermediate", "advanced"]
    sentiment: Literal["confused", "curious", "confident", "frustrated"]


# Tool Schemas (simulate a PDF-defined schema)
class NoteMakerRequest(BaseModel):
    subject: str
    topic: str
    key_points: List[str] = Field(default_factory=list)
    detail_level: Literal["brief", "standard", "in_depth"] = "standard"


class FlashcardGeneratorRequest(BaseModel):
    subject: str
    topic: str
    num_cards: int = Field(default=5, ge=1, le=50)
    style: Literal["basic", "cloze"] = "basic"


class ConceptExplainerRequest(BaseModel):
    subject: str
    concept: str
    target_level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    analogy_preference: Optional[str] = None


class ToolChoice(BaseModel):
    name: Literal["note_maker", "flashcard_generator", "concept_explainer"]
    parameters: Dict[str, Any]


# Chat Flow
class ChatRequest(BaseModel):
    user_id: Optional[int] = None
    chat_id: Optional[int] = None
    message: str


class ChatResponse(BaseModel):
    chosen_tool: str
    parameters: Dict[str, Any]
    result: Dict[str, Any]
    analysis: ContextAnalysis


class HealthResponse(BaseModel):
    status: str = "ok"
