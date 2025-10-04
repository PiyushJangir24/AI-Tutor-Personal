from __future__ import annotations

from typing import Dict, Any, List
from .schemas import (
    NoteMakerRequest,
    FlashcardGeneratorRequest,
    ConceptExplainerRequest,
)


async def call_note_maker(params: Dict[str, Any]) -> Dict[str, Any]:
    req = NoteMakerRequest(**params)
    notes_lines: List[str] = [f"# Notes: {req.subject.title()} - {req.topic.title()} ({req.detail_level})"]
    if req.key_points:
        notes_lines.append("Key Points:")
        for idx, kp in enumerate(req.key_points, 1):
            notes_lines.append(f"{idx}. {kp}")
    else:
        notes_lines.append("No key points provided. Auto-generated outline:")
        notes_lines.extend([
            "1. Definition",
            "2. Examples",
            "3. Common pitfalls",
            "4. Practice questions"
        ])
    return {"type": "notes", "content": "\n".join(notes_lines)}


async def call_flashcard_generator(params: Dict[str, Any]) -> Dict[str, Any]:
    req = FlashcardGeneratorRequest(**params)
    cards = []
    for i in range(1, req.num_cards + 1):
        if req.style == "cloze":
            front = f"{req.topic} is {{c1::...}}"
            back = f"{req.topic} relates to {req.subject} (card {i})"
        else:
            front = f"What is {req.topic}?"
            back = f"An explanation in {req.subject} context (card {i})."
        cards.append({"front": front, "back": back})
    return {"type": "flashcards", "cards": cards}


async def call_concept_explainer(params: Dict[str, Any]) -> Dict[str, Any]:
    req = ConceptExplainerRequest(**params)
    explanation = [
        f"Explaining {req.concept} for a {req.target_level} student in {req.subject}.",
        "Definition: ...",
        "Intuition: ...",
        "Example: ...",
    ]
    if req.analogy_preference:
        explanation.append(f"Using analogy: {req.analogy_preference}.")
    return {"type": "explanation", "content": "\n".join(explanation)}
