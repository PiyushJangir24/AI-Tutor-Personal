from __future__ import annotations
from typing import Dict, Any, Tuple, TypedDict, Optional
import re
from pydantic import ValidationError
from fastapi import HTTPException
from schemas import (
    AnalysisResult,
    OrchestrationRequest,
    NoteMakerInput, FlashcardGeneratorInput, ConceptExplainerInput,
)
from langgraph.graph import StateGraph, START, END
import httpx


SUBJECT_ALIASES = {
    "math": ["calculus", "algebra", "geometry", "derivative", "integral"],
    "physics": ["force", "motion", "newton", "energy", "thermodynamics"],
    "biology": ["cell", "dna", "genetics", "evolution"],
    "chemistry": ["atom", "molecule", "reaction", "stoichiometry"],
}


def _infer_subject(message: str) -> str:
    text = message.lower()
    for subject, keywords in SUBJECT_ALIASES.items():
        if subject in text:
            return subject
        if any(kw in text for kw in keywords):
            return subject
    return "math"  # default


def _infer_difficulty(message: str) -> str:
    text = message.lower()
    if any(w in text for w in ["beginner", "intro", "basic", "simple"]):
        return "beginner"
    if any(w in text for w in ["advanced", "complex", "proof", "rigorous"]):
        return "advanced"
    return "intermediate"


def _infer_emotion(message: str) -> str:
    text = message.lower()
    if any(w in text for w in ["stuck", "confused", "lost", "don't get", "dont get", "help!"]):
        return "confused"
    if any(w in text for w in ["frustrated", "annoyed", "angry"]):
        return "frustrated"
    if any(w in text for w in ["curious", "wondering", "interested"]):
        return "curious"
    if any(w in text for w in ["got it", "understand", "confident"]):
        return "confident"
    return "neutral"


def _infer_intent_and_topic(message: str) -> Tuple[str, str]:
    text = message.lower()
    # Intent heuristics
    if re.search(r"\bflash(card|cards)\b|drill|quiz|practice", text):
        intent = "flashcard_generator"
    elif re.search(r"\b(note|notes|summary|outline)\b", text):
        intent = "note_maker"
    elif re.search(r"\bexplain|what is|how does|why\b", text):
        intent = "concept_explainer"
    else:
        # default to explainer if asking questions; otherwise notes
        intent = "concept_explainer" if "?" in text or text.startswith("what") else "note_maker"

    # Topic extraction heuristic: pick longest noun-like phrase
    topic_match = re.findall(r"[a-zA-Z][a-zA-Z\s\-]{3,}", text)
    topic = max(topic_match, key=len).strip() if topic_match else "general topic"
    return intent, topic


def analyze_message(req: OrchestrationRequest) -> AnalysisResult:
    subject = _infer_subject(req.message)
    difficulty = _infer_difficulty(req.message)
    emotion = _infer_emotion(req.message)
    intent, topic = _infer_intent_and_topic(req.message)
    return AnalysisResult(subject=subject, topic=topic, difficulty=difficulty, emotion=emotion, intent=intent)


def extract_params(analysis: AnalysisResult, message: str) -> Dict[str, Any]:
    if analysis.intent == "note_maker":
        return {
            "subject": analysis.subject,
            "topic": analysis.topic or "general",
            "key_points": [],
            "difficulty": analysis.difficulty,
            "length": "medium",
            "style": "bullets",
        }
    if analysis.intent == "flashcard_generator":
        # heuristic for number
        num = 10
        m = re.search(r"(\d+)[-\s]*(cards|flashcards)", message.lower())
        if m:
            try:
                num = int(m.group(1))
            except Exception:
                pass
        return {
            "subject": analysis.subject,
            "topic": analysis.topic or "core concepts",
            "num_cards": max(1, min(50, num)),
            "difficulty": analysis.difficulty,
            "format": "qna",
            "key_terms": [],
        }
    if analysis.intent == "concept_explainer":
        return {
            "subject": analysis.subject,
            "concept": analysis.topic or "concept",
            "level": analysis.difficulty,
            "analogy": analysis.emotion in {"confused", "frustrated"},
        }
    return {}


def validate_and_route(params: Dict[str, Any], intent: str) -> Tuple[str, Dict[str, Any]]:
    try:
        if intent == "note_maker":
            payload = NoteMakerInput(**params)
            return "/note_maker", payload.model_dump()
        if intent == "flashcard_generator":
            payload = FlashcardGeneratorInput(**params)
            return "/flashcard_generator", payload.model_dump()
        if intent == "concept_explainer":
            payload = ConceptExplainerInput(**params)
            return "/concept_explainer", payload.model_dump()
    except ValidationError as e:
        raise HTTPException(status_code=422, detail={"error": "validation_error", "details": e.errors()})

    raise HTTPException(status_code=400, detail={"error": "unknown_intent"})


# ---------------- LangGraph Pipeline -----------------
class PipelineState(TypedDict, total=False):
    message: str
    analysis: AnalysisResult
    params: Dict[str, Any]
    route_path: str
    payload: Dict[str, Any]
    result: Dict[str, Any]


def _node_analyze(state: PipelineState) -> PipelineState:
    req = OrchestrationRequest(message=state["message"])  # type: ignore[index]
    analysis = analyze_message(req)
    return {"analysis": analysis}


def _node_extract(state: PipelineState) -> PipelineState:
    analysis = state["analysis"]
    params = extract_params(analysis, state["message"])  # type: ignore[index]
    return {"params": params}


def _node_validate(state: PipelineState) -> PipelineState:
    analysis = state["analysis"]
    route_path, payload = validate_and_route(state["params"], analysis.intent)  # type: ignore[index]
    return {"route_path": route_path, "payload": payload}


async def _node_call(state: PipelineState) -> PipelineState:
    url = f"http://localhost:8000{state['route_path']}"
    async with httpx.AsyncClient() as client:
        r = await client.post(url, json=state["payload"], timeout=20)
        r.raise_for_status()
        return {"result": r.json()}


_GRAPH = None


def get_graph():
    global _GRAPH
    if _GRAPH is not None:
        return _GRAPH
    graph = StateGraph(PipelineState)
    graph.add_node("analyze", _node_analyze)
    graph.add_node("extract", _node_extract)
    graph.add_node("validate", _node_validate)
    graph.add_node("call", _node_call)

    graph.add_edge(START, "analyze")
    graph.add_edge("analyze", "extract")
    graph.add_edge("extract", "validate")
    graph.add_edge("validate", "call")
    graph.add_edge("call", END)
    _GRAPH = graph.compile()
    return _GRAPH


async def run_pipeline(message: str) -> PipelineState:
    graph = get_graph()
    state: PipelineState = {"message": message}
    out: PipelineState = await graph.ainvoke(state)
    out["message"] = message
    return out
