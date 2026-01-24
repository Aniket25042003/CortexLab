"""
Trend Synthesizer Agent Node

Analyzes papers to identify research themes and trends.
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


TREND_SYNTHESIZER_PROMPT = """You are a research trend synthesizer. Analyze the following papers and identify major themes and trends in this research area.

Papers (title, year, abstract):
{papers_text}

Analyze these papers and identify:
1. Major Themes: Group papers into thematic clusters (methods, datasets, evaluation approaches, applications)
2. Current Trends: What's gaining traction? What methods/approaches are becoming popular?
3. Saturation Indicators: Which areas seem well-explored vs under-explored?

Respond in JSON format:
{{
    "themes": [
        {{
            "name": "theme name",
            "description": "brief description",
            "paper_count": number,
            "representative_papers": ["paper titles"],
            "key_methods": ["method names"]
        }}
    ],
    "trends": {{
        "hot_topics": ["topics gaining momentum"],
        "declining": ["topics losing interest"],
        "steady": ["consistently researched areas"]
    }},
    "saturation": {{
        "well_explored": ["areas with lots of work"],
        "emerging": ["newer areas with less work"],
        "under_explored": ["potential opportunity areas"]
    }}
}}
"""


async def trend_synthesizer_node(state: DiscoveryState) -> DiscoveryState:
    """
    Synthesize trends from retrieved papers.
    
    Input: papers list
    Output: themes, trends analysis
    """
    papers = state.get("papers", [])
    
    if not papers:
        return {
            **state,
            "error": "No papers to analyze",
            "current_step": "error",
        }
    
    # Prepare papers text for LLM
    papers_text = "\n\n".join([
        f"Title: {p.get('title', 'Unknown')}\n"
        f"Year: {p.get('year', 'Unknown')}\n"
        f"Abstract: {p.get('abstract', 'No abstract')[:500]}..."
        for p in papers[:30]  # Limit to 30 papers to fit context
    ])
    
    logger.info(f"[TREND_SYNTHESIZER] Analyzing {len(papers)} papers...")
    
    from app.agents.llm_factory import get_llm
    llm = get_llm(model_name="kimi", temperature=0.3)
    
    prompt = ChatPromptTemplate.from_template(TREND_SYNTHESIZER_PROMPT)
    chain = prompt | llm
    
    try:
        response = await chain.ainvoke({"papers_text": papers_text})
        
        result = parse_json(response.content)
        
        logger.info(f"[TREND_SYNTHESIZER] Identified {len(result.get('themes', []))} themes")
        
        return {
            **state,
            "themes": result.get("themes", []),
            "trends": result.get("trends", {}),
            "current_step": "trends_identified",
            "messages": state.get("messages", []) + [{
                "type": "agent_note",
                "agent": "trend_synthesizer",
                "content": f"Identified {len(result.get('themes', []))} research themes"
            }]
        }
    except Exception as e:
        logger.error(f"[TREND_SYNTHESIZER] Failed: {e}")
        return {
            **state,
            "error": f"Trend synthesis failed: {str(e)}",
            "current_step": "error",
        }
