from __future__ import annotations

from .schemas import ContextAnalysis


def simple_context_analysis(message: str) -> ContextAnalysis:
    lower = message.lower()

    subject = "general"
    if any(x in lower for x in ["math", "algebra", "calculus", "equation", "derivative"]):
        subject = "math"
    elif any(x in lower for x in ["biology", "cell", "evolution", "photosynthesis"]):
        subject = "biology"
    elif any(x in lower for x in ["physics", "force", "energy", "quantum"]):
        subject = "physics"
    elif any(x in lower for x in ["history", "revolution", "war", "empire"]):
        subject = "history"

    # Topic extraction: choose last noun-ish token as a naive heuristic
    topic = ""
    tokens = [t.strip(".,!?") for t in lower.split()]
    if tokens:
        topic = tokens[-1]
    if "about" in tokens:
        idx = tokens.index("about")
        topic = tokens[idx + 1] if idx + 1 < len(tokens) else topic

    # Difficulty guess
    difficulty = "beginner"
    if any(x in lower for x in ["hard", "difficult", "advanced", "proof", "theorem"]):
        difficulty = "advanced"
    elif any(x in lower for x in ["intermediate", "somewhat", "medium"]):
        difficulty = "intermediate"

    # Sentiment/emotional state
    sentiment = "curious"
    if any(x in lower for x in ["confused", "don't get", "dont get", "lost"]):
        sentiment = "confused"
    elif any(x in lower for x in ["frustrated", "annoyed", "angry"]):
        sentiment = "frustrated"
    elif any(x in lower for x in ["i know", "easy", "got it"]):
        sentiment = "confident"

    return ContextAnalysis(subject=subject, topic=topic or "general", difficulty=difficulty, sentiment=sentiment)
