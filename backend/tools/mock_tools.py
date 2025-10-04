from __future__ import annotations
from typing import List
from fastapi import APIRouter
from schemas import (
    NoteMakerInput, NoteMakerOutput,
    FlashcardGeneratorInput, FlashcardGeneratorOutput, Flashcard,
    ConceptExplainerInput, ConceptExplainerOutput,
)

router = APIRouter(tags=["tools"])


def _bullet(text: str) -> str:
    return f"- {text}" if not text.startswith("-") else text


@router.post("/note_maker", response_model=NoteMakerOutput)
async def note_maker(payload: NoteMakerInput) -> NoteMakerOutput:
    header = f"Notes on {payload.topic} ({payload.subject}) — {payload.difficulty.title()}"
    outline: List[str] = []
    if payload.style in {"outline", "bullets"}:
        outline = [f"{i+1}. {kp}" for i, kp in enumerate(payload.key_points[:10])] if payload.key_points else []
    body_points = payload.key_points or [payload.topic]

    length_map = {"short": 4, "medium": 8, "long": 14}
    target_points = length_map.get(payload.length, 8)

    bullets = [
        _bullet(f"Key idea: {kp}") for kp in body_points
    ]
    while len(bullets) < target_points:
        bullets.append(_bullet(f"Detail {len(bullets)+1} about {payload.topic}"))

    notes_text = "\n".join([header, "", *bullets, "", "Summary: These notes provide a concise overview."])
    return NoteMakerOutput(notes=notes_text, outline=outline or None)


@router.post("/flashcard_generator", response_model=FlashcardGeneratorOutput)
async def flashcard_generator(payload: FlashcardGeneratorInput) -> FlashcardGeneratorOutput:
    base = payload.topic
    cards: List[Flashcard] = []
    for i in range(payload.num_cards):
        if payload.format == "qna":
            q = f"({payload.difficulty}) What is {base}? (card {i+1})"
            a = f"{base} is a concept in {payload.subject}."
        else:
            q = f"({payload.difficulty}) {base} is a concept in _____. (card {i+1})"
            a = payload.subject
        cards.append(Flashcard(question=q, answer=a))
    return FlashcardGeneratorOutput(cards=cards)


@router.post("/concept_explainer", response_model=ConceptExplainerOutput)
async def concept_explainer(payload: ConceptExplainerInput) -> ConceptExplainerOutput:
    explanation = (
        f"Explaining {payload.concept} in {payload.subject} for a {payload.level} learner. "
        f"{ 'Imagine it like a familiar analogy. ' if payload.analogy else ''}"
        f"Core idea: {payload.concept} relates to foundational principles in {payload.subject}."
    )
    return ConceptExplainerOutput(explanation=explanation)
