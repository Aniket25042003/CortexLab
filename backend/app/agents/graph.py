"""
Agent Graph Definition

Main LangGraph state machine for research agent workflows.
All graphs include conditional error routing to short-circuit on failure.
"""

from typing import Literal
from langgraph.graph import StateGraph, END

from app.agents.state import DiscoveryState, DeepDiveState, PaperState


# ── Routing helpers ────────────────────────────────────────────────────────────

def _route_or_error(next_node: str):
    """Return a conditional-edge function that routes to *next_node* or END on error."""
    def _router(state: dict) -> Literal["continue", "end"]:
        if state.get("current_step") == "error" or state.get("error"):
            return "end"
        return "continue"
    _router.__name__ = f"route_after_{next_node}"
    return _router


# ── Discovery graph ────────────────────────────────────────────────────────────

def create_discovery_graph():
    """
    Discovery pipeline:
      ScopeClarifier → LiteratureScout → TrendSynthesizer → GapMiner → DirectionGenerator

    Each step checks for errors and short-circuits to END if one is found.
    """
    from app.agents.nodes.scope_clarifier import scope_clarifier_node
    from app.agents.nodes.literature_scout import literature_scout_node
    from app.agents.nodes.trend_synthesizer import trend_synthesizer_node
    from app.agents.nodes.gap_miner import gap_miner_node
    from app.agents.nodes.direction_generator import direction_generator_node

    graph = StateGraph(DiscoveryState)

    # Nodes
    graph.add_node("scope_clarifier",    scope_clarifier_node)
    graph.add_node("literature_scout",   literature_scout_node)
    graph.add_node("trend_synthesizer",  trend_synthesizer_node)
    graph.add_node("gap_miner",          gap_miner_node)
    graph.add_node("direction_generator", direction_generator_node)

    # Entry
    graph.set_entry_point("scope_clarifier")

    # Conditional edges — bail out on any error
    graph.add_conditional_edges(
        "scope_clarifier",
        _route_or_error("scope_clarifier"),
        {"continue": "literature_scout", "end": END},
    )
    graph.add_conditional_edges(
        "literature_scout",
        _route_or_error("literature_scout"),
        {"continue": "trend_synthesizer", "end": END},
    )
    graph.add_conditional_edges(
        "trend_synthesizer",
        _route_or_error("trend_synthesizer"),
        {"continue": "gap_miner", "end": END},
    )
    graph.add_conditional_edges(
        "gap_miner",
        _route_or_error("gap_miner"),
        {"continue": "direction_generator", "end": END},
    )
    graph.add_edge("direction_generator", END)

    return graph.compile()


# ── Deep-dive graph ────────────────────────────────────────────────────────────

def create_deep_dive_graph():
    """
    Deep dive pipeline:
      DeepDiveScout → ExperimentDesigner
    """
    from app.agents.nodes.deep_dive_scout import deep_dive_scout_node
    from app.agents.nodes.experiment_designer import experiment_designer_node

    graph = StateGraph(DeepDiveState)

    graph.add_node("deep_dive_scout",      deep_dive_scout_node)
    graph.add_node("experiment_designer",  experiment_designer_node)

    graph.set_entry_point("deep_dive_scout")
    graph.add_conditional_edges(
        "deep_dive_scout",
        _route_or_error("deep_dive_scout"),
        {"continue": "experiment_designer", "end": END},
    )
    graph.add_edge("experiment_designer", END)

    return graph.compile()


# ── Paper graph ────────────────────────────────────────────────────────────────

def create_paper_graph():
    """
    Paper drafting pipeline:
      PaperWriter → PaperEditor
    """
    from app.agents.nodes.paper_writer import paper_writer_node
    from app.agents.nodes.paper_editor import paper_editor_node

    graph = StateGraph(PaperState)

    graph.add_node("paper_writer", paper_writer_node)
    graph.add_node("paper_editor", paper_editor_node)

    graph.set_entry_point("paper_writer")
    graph.add_conditional_edges(
        "paper_writer",
        _route_or_error("paper_writer"),
        {"continue": "paper_editor", "end": END},
    )
    graph.add_edge("paper_editor", END)

    return graph.compile()
