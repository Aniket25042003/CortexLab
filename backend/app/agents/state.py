"""
Agent State Definitions

Defines the state that flows through the agent graph.
"""

from typing import TypedDict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class Paper:
    """Represents an academic paper."""
    id: str
    title: str
    authors: str
    year: int
    abstract: str
    url: str
    venue: Optional[str] = None
    citation_count: Optional[int] = None
    provider: str = "semantic_scholar"


@dataclass
class ResearchGap:
    """Represents an identified research gap."""
    id: str
    description: str
    category: str  # under-explored, evaluation_blind_spot, robustness, data_constraint
    evidence: List[str]  # Paper IDs that support this gap
    confidence: float  # 0-1


@dataclass
class ResearchDirection:
    """Represents a proposed research direction."""
    id: str
    title: str
    description: str
    novelty_angle: str
    feasibility_score: int  # 1-10
    contribution_type: str  # method, benchmark, analysis
    minimum_experiments: List[str]
    related_gaps: List[str]  # Gap IDs


class DiscoveryState(TypedDict):
    """State for the discovery agent pipeline."""
    # Input
    user_query: str
    project_id: str
    
    # Scope Clarifier output
    domain_boundaries: Optional[dict]
    search_queries: Optional[List[str]]
    constraints: Optional[dict]
    
    # Literature Scout output
    papers: Optional[List[dict]]
    
    # Trend Synthesizer output
    themes: Optional[List[dict]]
    trends: Optional[dict]
    
    # Gap Miner output
    gaps: Optional[List[dict]]
    
    # Direction Generator output
    directions: Optional[List[dict]]
    
    # Metadata
    current_step: str
    error: Optional[str]
    messages: List[dict]  # For streaming updates


class DeepDiveState(TypedDict):
    """State for the deep dive agent pipeline."""
    # Input
    project_id: str
    direction: dict
    
    # Deep Dive Scout output
    baseline_methods: Optional[List[dict]]
    datasets: Optional[List[dict]]
    metrics: Optional[List[dict]]  # Changed to List[dict] to match reality
    failure_cases: Optional[List[dict]] # Changed to List[dict] to match reality
    deep_dive_papers: Optional[List[dict]]
    implementation_notes: Optional[dict]
    
    # Experiment Designer output
    hypotheses: Optional[List[dict]]
    ablations: Optional[List[dict]]
    training_protocol: Optional[dict]
    evaluation_plan: Optional[dict]
    compute_estimate: Optional[dict]
    proposed_method: Optional[dict]
    experiment_setup: Optional[dict]
    timeline: Optional[dict]
    risks: Optional[List[dict]]
    
    # Metadata
    current_step: str
    error: Optional[str]
    messages: List[dict]


class PaperState(TypedDict):
    """State for the paper drafting agent pipeline."""
    # Input
    project_id: str
    direction: dict
    deep_dive_report: str
    experiment_data: List[dict]
    
    # Paper Writer output
    outline: Optional[dict]
    title: Optional[str]
    abstract: Optional[str]
    introduction: Optional[str]
    related_work: Optional[str]
    method: Optional[str]
    experiments: Optional[str]
    results: Optional[str]
    discussion: Optional[str]
    conclusion: Optional[str]
    references: Optional[List[dict]]
    
    # Full paper
    paper_markdown: Optional[str]
    
    # Metadata
    current_step: str
    error: Optional[str]
    messages: List[dict]
