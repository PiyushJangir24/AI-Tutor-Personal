from __future__ import annotations

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from .schemas import ToolChoice
from .analysis import simple_context_analysis
from . import tools as tool_calls


class OrchestratorState(BaseModel):
    message: str
    analysis: Dict[str, Any] | None = None
    tool_choice: ToolChoice | None = None
    result: Dict[str, Any] | None = None

    class Config:
        arbitrary_types_allowed = True


def select_tool(analysis: Dict[str, Any], message: str) -> ToolChoice:
    lower = message.lower()

    if any(word in lower for word in ["note", "notes", "summarize", "summary"]):
        params = {
            "subject": analysis["subject"],
            "topic": analysis["topic"],
            "key_points": [],
            "detail_level": "standard",
        }
        return ToolChoice(name="note_maker", parameters=params)

    if any(word in lower for word in ["flashcard", "cards", "quiz"]):
        params = {
            "subject": analysis["subject"],
            "topic": analysis["topic"],
            "num_cards": 5,
            "style": "basic",
        }
        return ToolChoice(name="flashcard_generator", parameters=params)

    # Default to concept explainer
    params = {
        "subject": analysis["subject"],
        "concept": analysis["topic"],
        "target_level": analysis["difficulty"],
        "analogy_preference": None,
    }
    return ToolChoice(name="concept_explainer", parameters=params)


async def exec_tool(tool_choice: ToolChoice) -> Dict[str, Any]:
    if tool_choice.name == "note_maker":
        return await tool_calls.call_note_maker(tool_choice.parameters)
    if tool_choice.name == "flashcard_generator":
        return await tool_calls.call_flashcard_generator(tool_choice.parameters)
    if tool_choice.name == "concept_explainer":
        return await tool_calls.call_concept_explainer(tool_choice.parameters)
    raise ValueError("Unknown tool")


def build_graph():
    graph = StateGraph(OrchestratorState)

    async def analyze_node(state: OrchestratorState):
        analysis = simple_context_analysis(state.message).model_dump()
        return {"analysis": analysis}

    async def choose_tool_node(state: OrchestratorState):
        assert state.analysis is not None
        tool_choice = select_tool(state.analysis, state.message)
        return {"tool_choice": tool_choice}

    async def run_tool_node(state: OrchestratorState):
        assert state.tool_choice is not None
        result = await exec_tool(state.tool_choice)
        return {"result": result}

    graph.add_node("analyze", analyze_node)
    graph.add_node("choose_tool", choose_tool_node)
    graph.add_node("run_tool", run_tool_node)

    graph.set_entry_point("analyze")
    graph.add_edge("analyze", "choose_tool")
    graph.add_edge("choose_tool", "run_tool")
    graph.add_edge("run_tool", END)

    return graph.compile()
