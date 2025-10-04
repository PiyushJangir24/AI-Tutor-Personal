from __future__ import annotations
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


# ----- Tool Schemas -----
class NoteMakerInput(BaseModel):
    subject: str = Field(..., examples=["math", "physics"]) 
    topic: str = Field(..., examples=["derivatives", "newton's laws"]) 
    key_points: List[str] = Field(default_factory=list)
    difficulty: Literal["beginner", "intermediate", "advanced"] = "beginner"
    length: Literal["short", "medium", "long"] = "medium"
    style: Literal["bullets", "outline", "summary"] = "bullets"


class NoteMakerOutput(BaseModel):
    notes: str
    outline: Optional[List[str]] = None


class Flashcard(BaseModel):
    question: str
    answer: str


class FlashcardGeneratorInput(BaseModel):
    subject: str
    topic: str
    num_cards: int = Field(10, ge=1, le=50)
    difficulty: Literal["beginner", "intermediate", "advanced"] = "beginner"
    format: Literal["qna", "cloze"] = "qna"
    key_terms: List[str] = Field(default_factory=list)


class FlashcardGeneratorOutput(BaseModel):
    cards: List[Flashcard]


class ConceptExplainerInput(BaseModel):
    subject: str
    concept: str
    level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    analogy: bool = False


class ConceptExplainerOutput(BaseModel):
    explanation: str


# ----- Orchestration -----
class OrchestrationRequest(BaseModel):
    message: str
    user_id: Optional[str] = None


class AnalysisResult(BaseModel):
    subject: str
    topic: Optional[str] = None
    difficulty: Literal["beginner", "intermediate", "advanced"]
    emotion: Literal["confused", "frustrated", "curious", "confident", "neutral"]
    intent: Literal["note_maker", "flashcard_generator", "concept_explainer"]


class OrchestrationResponse(BaseModel):
    user_id: str
    chosen_tool: Literal["note_maker", "flashcard_generator", "concept_explainer"]
    extracted_parameters: Dict[str, Any]
    result: Dict[str, Any]
    analysis: AnalysisResult


# ----- DB Schemas (API) -----
class ChatMessageResponse(BaseModel):
    id: int
    role: Literal["user", "assistant", "system"]
    content: str
    tool_used: Optional[str]
    params: Optional[Dict[str, Any]]


class MasteryResponse(BaseModel):
    subject: str
    level: float
