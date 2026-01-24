"""
Direction Generator Agent Node

Converts research gaps into actionable research directions.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from app.config import get_settings
from app.agents.state import DiscoveryState
from app.agents.utils import parse_json
import json

import logging

logger = logging.getLogger(__name__)
settings = get_settings()


DIRECTION_GENERATOR_PROMPT = """You are a research direction generator. Convert identified research gaps into concrete, actionable research directions.

Research Domain: {domain}

Identified Themes:
{themes_text}

Identified Gaps:
{gaps_text}

For each promising gap, generate a research direction that a PhD student or researcher could pursue. Each direction should be:
1. Specific and actionable
2. Feasible within 3-6 months
3. Novel enough to be publishable
4. Clear about expected contribution

Respond in JSON format:
{{
    "directions": [
        {{
            "id": "dir_1",
            "title": "Clear, specific title",
            "description": "Detailed description of the research direction",
            "novelty_angle": "What makes this novel/different",
            "feasibility_score": 8,
            "contribution_type": "method|benchmark|analysis|application",
            "minimum_experiments": [
                "Experiment 1 description",
                "Experiment 2 description"
            ],
            "expected_outcomes": ["what you'd expect to achieve"],
            "related_gap_ids": ["gap_1"],
            "estimated_timeline": "3-6 months",
            "required_resources": "compute/data requirements"
        }}
    ]
}}

Generate 5-8 diverse research directions ranked by feasibility and impact.
"""


async def direction_generator_node(state: DiscoveryState) -> DiscoveryState:
    """
    Generate research directions from gaps.
    
    Input: gaps, domain_boundaries
    Output: directions list
    """
    gaps = state.get("gaps", [])
    themes = state.get("themes", [])
    domain = state.get("domain_boundaries", {})
    
    # Fallback to themes if no gaps found
    use_fallback = False
    if not gaps:
        if not themes:
            return {
                **state,
                "error": "No gaps or themes to generate directions from",
                "current_step": "error",
            }
        use_fallback = True
        logger.warning("[DIRECTION_GENERATOR] No gaps found, falling back to theme-based generation")
    
    gaps_text = json.dumps(gaps, indent=2) if gaps else "No specific gaps identified."
    themes_text = json.dumps(themes, indent=2) if themes else "No specific themes identified."
    
    logger.info(f"[DIRECTION_GENERATOR] Generating directions from {len(gaps)} gaps...")

    from app.agents.llm_factory import get_llm
    llm = get_llm(model_name="qwen", temperature=0.5)
    
    prompt = ChatPromptTemplate.from_template(DIRECTION_GENERATOR_PROMPT)
    chain = prompt | llm
    
    try:
        response = await chain.ainvoke({
            "domain": json.dumps(domain),
            "gaps_text": gaps_text,
            "themes_text": themes_text,
        })
        
        result = parse_json(response.content)
        
        # Sort by feasibility score
        directions = result.get("directions", [])
        directions.sort(key=lambda x: x.get("feasibility_score", 0), reverse=True)
        
        logger.info(f"[DIRECTION_GENERATOR] Generated {len(directions)} directions")
        
        return {
            **state,
            "directions": directions,
            "current_step": "directions_generated",
            "messages": state.get("messages", []) + [{
                "type": "agent_note",
                "agent": "direction_generator",
                "content": f"Generated {len(directions)} research directions"
            }]
        }
    except Exception as e:
        logger.error(f"[DIRECTION_GENERATOR] Failed: {e}")
        return {
            **state,
            "error": f"Direction generation failed: {str(e)}",
            "current_step": "error",
        }
