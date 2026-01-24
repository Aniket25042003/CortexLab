"""
Paper Writer Agent Node

Generates a complete research paper draft in IMRaD format
from the research direction, experiment plan, and uploaded results.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from app.config import get_settings
from app.agents.state import PaperState
import json

settings = get_settings()


PAPER_OUTLINE_PROMPT = """You are an expert academic paper writer. Create a detailed outline for a research paper based on the following information.

## Research Direction
{direction_info}

## Experiment Plan Summary
{experiment_plan}

## Experiment Results
{experiment_results}

Create a comprehensive paper outline with section summaries.

Respond in JSON format:
{{
    "title": "Proposed paper title (clear, specific, includes key contribution)",
    "outline": {{
        "abstract": {{
            "purpose": "one sentence on paper goal",
            "method": "one sentence on approach",
            "results": "one sentence on key findings",
            "conclusion": "one sentence on significance"
        }},
        "introduction": {{
            "hook": "Opening to grab attention",
            "problem_statement": "What problem we address",
            "motivation": "Why this matters",
            "gap": "What's missing in current work",
            "contribution": ["list of contributions"],
            "paper_structure": "Brief roadmap"
        }},
        "related_work": {{
            "themes": [
                {{
                    "name": "theme name",
                    "description": "what this covers",
                    "key_papers": ["paper titles to cite"],
                    "our_difference": "how our work differs"
                }}
            ]
        }},
        "method": {{
            "overview": "High-level description",
            "components": [
                {{
                    "name": "component name",
                    "description": "detailed description",
                    "formulation": "mathematical formulation if applicable"
                }}
            ],
            "training": "Training procedure",
            "inference": "Inference procedure"
        }},
        "experiments": {{
            "setup": {{
                "datasets": "datasets used",
                "baselines": "methods compared against",
                "metrics": "evaluation metrics",
                "implementation": "implementation details"
            }},
            "main_results": "What main experiments show",
            "ablations": "What ablation studies reveal",
            "analysis": "Additional analysis points"
        }},
        "discussion": {{
            "findings": "Key takeaways",
            "limitations": "Honest limitations",
            "future_work": "Potential extensions"
        }},
        "conclusion": {{
            "summary": "Brief recap",
            "impact": "Broader implications"
        }}
    }}
}}
"""


SECTION_WRITER_PROMPT = """You are writing the {section_name} section of an academic research paper.

Paper Title: {title}

Section Outline:
{section_outline}

Context from other sections:
{context}

Experiment Data (if relevant):
{experiment_data}

Write this section in academic style. Be precise, clear, and well-structured.
Use LaTeX-style math notation where appropriate (e.g., $x^2$ for inline, $$equation$$ for display).
Include placeholder citations like [Author et al., Year] that can be filled in later.

Write the complete {section_name} section in Markdown format:
"""


async def paper_writer_node(state: PaperState) -> PaperState:
    """
    Write research paper draft from experiment results.
    
    Input: direction, deep_dive_report, experiment_data
    Output: paper_markdown (complete paper draft)
    """
    direction = state.get("direction", {})
    deep_dive_report = state.get("deep_dive_report", "")
    experiment_data = state.get("experiment_data", [])
    
    llm_flash = ChatGoogleGenerativeAI(
        model="gemini-flash-lite-latest",
        google_api_key=settings.google_api_key,
        temperature=0.3,
    )
    
    llm_pro = ChatGoogleGenerativeAI(
        model="gemini-flash-lite-latest",
        google_api_key=settings.google_api_key,
        temperature=0.4,
    )
    
    try:
        # Step 1: Generate paper outline
        outline_prompt = ChatPromptTemplate.from_template(PAPER_OUTLINE_PROMPT)
        outline_chain = outline_prompt | llm_flash
        
        # Format experiment data
        exp_data_text = ""
        if experiment_data:
            for exp in experiment_data:
                exp_data_text += f"\nFile: {exp.get('name', 'unknown')}\n"
                exp_data_text += f"Type: {exp.get('type', 'unknown')}\n"
                if exp.get('content'):
                    exp_data_text += f"Content Preview:\n{str(exp.get('content'))[:1000]}\n"
        else:
            exp_data_text = "No experiment results uploaded yet. Generate placeholder sections."
        
        outline_response = await outline_chain.ainvoke({
            "direction_info": json.dumps(direction, indent=2),
            "experiment_plan": deep_dive_report[:3000] if deep_dive_report else "No experiment plan provided",
            "experiment_results": exp_data_text,
        })
        
        # Parse outline
        outline_content = outline_response.content
        if "```json" in outline_content:
            outline_content = outline_content.split("```json")[1].split("```")[0]
        elif "```" in outline_content:
            outline_content = outline_content.split("```")[1].split("```")[0]
        
        outline = json.loads(outline_content.strip())
        title = outline.get("title", "Research Paper Draft")
        paper_outline = outline.get("outline", {})
        
        # Step 2: Write each section
        section_prompt = ChatPromptTemplate.from_template(SECTION_WRITER_PROMPT)
        section_chain = section_prompt | llm_pro
        
        sections = {}
        section_order = ["abstract", "introduction", "related_work", "method", "experiments", "discussion", "conclusion"]
        
        for section_name in section_order:
            section_outline = paper_outline.get(section_name, {})
            
            # Build context from previously written sections
            context = ""
            for prev_section in section_order:
                if prev_section == section_name:
                    break
                if prev_section in sections:
                    context += f"\n## {prev_section.title()}\n{sections[prev_section][:500]}...\n"
            
            section_response = await section_chain.ainvoke({
                "section_name": section_name.replace("_", " ").title(),
                "title": title,
                "section_outline": json.dumps(section_outline, indent=2),
                "context": context if context else "This is the first section.",
                "experiment_data": exp_data_text if section_name in ["experiments", "abstract", "conclusion"] else "Not applicable for this section.",
            })
            
            sections[section_name] = section_response.content
        
        # Step 3: Assemble the complete paper
        paper_markdown = f"""# {title}

## Abstract

{sections.get('abstract', 'Abstract pending.')}

---

## 1. Introduction

{sections.get('introduction', 'Introduction pending.')}

---

## 2. Related Work

{sections.get('related_work', 'Related work pending.')}

---

## 3. Method

{sections.get('method', 'Method pending.')}

---

## 4. Experiments

{sections.get('experiments', 'Experiments pending.')}

---

## 5. Discussion

{sections.get('discussion', 'Discussion pending.')}

---

## 6. Conclusion

{sections.get('conclusion', 'Conclusion pending.')}

---

## References

*References to be added based on citations in the text.*

"""
        
        return {
            **state,
            "title": title,
            "outline": paper_outline,
            "abstract": sections.get("abstract", ""),
            "introduction": sections.get("introduction", ""),
            "related_work": sections.get("related_work", ""),
            "method": sections.get("method", ""),
            "experiments": sections.get("experiments", ""),
            "discussion": sections.get("discussion", ""),
            "conclusion": sections.get("conclusion", ""),
            "paper_markdown": paper_markdown,
            "current_step": "paper_drafted",
            "messages": state.get("messages", []) + [
                {
                    "type": "agent_note",
                    "agent": "paper_writer",
                    "content": f"Generated paper draft: '{title}' with {len(section_order)} sections"
                }
            ]
        }
        
    except Exception as e:
        return {
            **state,
            "error": f"Paper writing failed: {str(e)}",
            "current_step": "error",
        }
