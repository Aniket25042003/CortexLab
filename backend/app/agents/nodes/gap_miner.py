"""
Gap Miner Agent Node

Extracts research gaps from papers and themes.
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


GAP_MINER_PROMPT = """You are a research gap mining expert. Based on the papers and identified themes, extract concrete research gaps and opportunities.

Research Domain: {domain}

Identified Themes:
{themes_text}

Key Papers (with abstracts):
{papers_text}

Saturation Analysis:
- Well explored: {well_explored}
- Under explored: {under_explored}

Identify research gaps by looking for:
1. Limitations mentioned in paper abstracts
2. "Future work" suggestions
3. Cross-theme opportunities (combining approaches from different themes)
4. Methodological gaps (missing baselines, incomplete evaluations)
5. Data/benchmark gaps
6. Generalization failures

Respond in JSON format:
{{
    "gaps": [
        {{
            "id": "gap_1",
            "title": "short title",
            "description": "detailed description of the gap",
            "category": "under_explored|evaluation_blind_spot|robustness|data_constraint|methodological",
            "evidence": ["paper titles that support this gap"],
            "potential_impact": "high|medium|low",
            "confidence": 0.8
        }}
    ]
}}

Identify 5-10 concrete, actionable research gaps.
"""


async def gap_miner_node(state: DiscoveryState) -> DiscoveryState:
    """
    Extract research gaps from papers and themes.
    
    Input: papers, themes, trends
    Output: gaps list
    """
    papers = state.get("papers", [])
    themes = state.get("themes", [])
    trends = state.get("trends", {})
    domain = state.get("domain_boundaries", {})
    
    # Prepare inputs
    themes_text = json.dumps(themes, indent=2) if themes else "No themes identified"
    papers_text = "\n\n".join([
        f"Title: {p.get('title', 'Unknown')}\n"
        f"Abstract: {p.get('abstract', 'No abstract')[:400]}..."
        for p in papers[:20]
    ])
    
    saturation = trends.get("saturation", {})
    well_explored = ", ".join(saturation.get("well_explored", ["None identified"]))
    under_explored = ", ".join(saturation.get("under_explored", ["None identified"]))
    
    logger.info(f"[GAP_MINER] Mining gaps from {len(themes)} themes and {len(papers)} papers...")

    from app.agents.llm_factory import get_llm
    llm = get_llm(model_name="gpt_oss", temperature=0.4)
    
    prompt = ChatPromptTemplate.from_template(GAP_MINER_PROMPT)
    chain = prompt | llm
    
    try:
        response = await chain.ainvoke({
            "domain": json.dumps(domain),
            "themes_text": themes_text,
            "papers_text": papers_text,
            "well_explored": well_explored,
            "under_explored": under_explored,
        })
        
        result = parse_json(response.content)
        
        logger.info(f"[GAP_MINER] Identified {len(result.get('gaps', []))} gaps")
        
        return {
            **state,
            "gaps": result.get("gaps", []),
            "current_step": "gaps_identified",
            "messages": state.get("messages", []) + [{
                "type": "agent_note",
                "agent": "gap_miner",
                "content": f"Identified {len(result.get('gaps', []))} research gaps"
            }]
        }
    except Exception as e:
        logger.error(f"[GAP_MINER] Failed: {e}")
        return {
            **state,
            "error": f"Gap mining failed: {str(e)}",  
            "current_step": "error",
        }
