"""
Paper Editor Agent Node

Refines and improves the paper draft based on user instructions,
handling revisions for style, clarity, length, and content.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from app.config import get_settings
from app.agents.state import PaperState
from app.agents.utils import parse_json
import json
import re

settings = get_settings()


EDITOR_ANALYSIS_PROMPT = """You are an expert academic paper editor. Analyze this paper draft and identify areas for improvement.

## Paper Draft:
{paper_markdown}

## User's Revision Instructions (if any):
{revision_instructions}

Analyze the paper and provide:
1. Overall quality assessment
2. Specific issues to address
3. Section-by-section recommendations

RESPONDING WITH VALID JSON IS CRITICAL.
Ensure all backslashes in your JSON strings are properly escaped (e.g., use "\\alpha" instead of "\alpha").

Respond in JSON format:
{{
    "quality_score": 7,
    "overall_assessment": "Brief overall assessment",
    "strengths": ["list of strengths"],
    "weaknesses": ["list of weaknesses"],
    "section_feedback": {{
        "abstract": {{
            "issues": ["list of issues"],
            "suggestions": ["how to improve"]
        }},
        "introduction": {{
            "issues": [],
            "suggestions": []
        }},
        "related_work": {{
            "issues": [],
            "suggestions": []
        }},
        "method": {{
            "issues": [],
            "suggestions": []
        }},
        "experiments": {{
            "issues": [],
            "suggestions": []
        }},
        "discussion": {{
            "issues": [],
            "suggestions": []
        }},
        "conclusion": {{
            "issues": [],
            "suggestions": []
        }}
    }},
    "priority_revisions": [
        {{
            "section": "section name",
            "issue": "what needs fixing",
            "priority": "high/medium/low"
        }}
    ]
}}
"""


SECTION_REVISION_PROMPT = """You are revising a section of an academic research paper.

## Original Section Content:
{section_content}

## Revision Instructions:
{revision_instructions}

## Specific Issues to Address:
{issues}

## Suggestions:
{suggestions}

Rewrite this section addressing all the issues and following the instructions.
Maintain academic tone and proper structure.
Keep citations in [Author et al., Year] format.

Revised section:
"""


STYLE_ADAPTATION_PROMPT = """Adapt this paper to follow {style_guide} formatting and style conventions.

## Current Paper:
{paper_markdown}

## Style Requirements:
- Follow {style_guide} citation style
- Use appropriate section numbering
- Adjust language conventions as needed
- Ensure proper formatting

Rewrite the paper following these conventions. Output the complete revised paper in Markdown:
"""


async def paper_editor_node(state: PaperState) -> PaperState:
    """
    Edit and refine paper draft based on user instructions.
    
    Handles various editing modes:
    - General improvement (no specific instructions)
    - Style adaptation (IEEE, ACL, NeurIPS, etc.)
    - Length adjustment (expand/condense)
    - Specific section revision
    - Clarity improvement
    
    Input: paper_markdown, revision_instructions (optional)
    Output: revised paper_markdown
    """
    paper_markdown = state.get("paper_markdown", "")
    revision_instructions = state.get("revision_instructions", "")
    
    if not paper_markdown:
        return {
            **state,
            "error": "No paper draft to edit",
            "current_step": "error",
        }
    
    from app.agents.llm_factory import get_llm
    llm = get_llm(model_name="gpt_oss", temperature=0.3)
    
    try:
        # Step 1: Analyze the paper
        analysis_prompt = ChatPromptTemplate.from_template(EDITOR_ANALYSIS_PROMPT)
        analysis_chain = analysis_prompt | llm
        
        analysis_response = await analysis_chain.ainvoke({
            "paper_markdown": paper_markdown[:15000],  # Limit for context
            "revision_instructions": revision_instructions or "General improvement - make the paper clearer and more compelling.",
        })
        
        analysis = parse_json(analysis_response.content)
        
        # Step 2: Check for style adaptation request
        style_guides = ["ieee", "acl", "neurips", "icml", "cvpr", "aaai", "emnlp", "naacl", "acm"]
        requested_style = None
        
        if revision_instructions:
            instruction_lower = revision_instructions.lower()
            for style in style_guides:
                if style in instruction_lower:
                    requested_style = style.upper()
                    break
        
        # Step 3: Perform revisions
        if requested_style:
            # Style adaptation mode
            style_prompt = ChatPromptTemplate.from_template(STYLE_ADAPTATION_PROMPT)
            style_chain = style_prompt | llm
            
            style_response = await style_chain.ainvoke({
                "paper_markdown": paper_markdown,
                "style_guide": requested_style,
            })
            
            revised_paper = style_response.content
            revision_summary = f"Adapted paper to {requested_style} style"
            
        else:
            # Section-by-section revision mode
            section_feedback = analysis.get("section_feedback", {})
            priority_revisions = analysis.get("priority_revisions", [])
            
            # Extract sections from the paper
            sections = extract_sections(paper_markdown)
            
            revision_prompt = ChatPromptTemplate.from_template(SECTION_REVISION_PROMPT)
            revision_chain = revision_prompt | llm
            
            revised_sections = {}
            sections_revised = 0
            
            for section_name, section_content in sections.items():
                feedback = section_feedback.get(section_name, {})
                issues = feedback.get("issues", [])
                suggestions = feedback.get("suggestions", [])
                
                # Only revise sections with issues or if user requested
                if issues or (revision_instructions and section_name.lower() in revision_instructions.lower()):
                    revision_response = await revision_chain.ainvoke({
                        "section_content": section_content,
                        "revision_instructions": revision_instructions or "Improve clarity and academic quality",
                        "issues": json.dumps(issues),
                        "suggestions": json.dumps(suggestions),
                    })
                    
                    revised_sections[section_name] = revision_response.content
                    sections_revised += 1
                else:
                    revised_sections[section_name] = section_content
            
            # Reassemble paper
            revised_paper = reassemble_paper(
                state.get("title", "Research Paper"),
                revised_sections
            )
            revision_summary = f"Revised {sections_revised} sections based on analysis"
        
        return {
            **state,
            "paper_markdown": revised_paper,
            "editor_analysis": analysis,
            "revision_summary": revision_summary,
            "current_step": "paper_edited",
            "messages": state.get("messages", []) + [
                {
                    "type": "agent_note",
                    "agent": "paper_editor",
                    "content": revision_summary
                }
            ]
        }
        
    except Exception as e:
        return {
            **state,
            "error": f"Paper editing failed: {str(e)}",
            "current_step": "error",
        }


def extract_sections(paper_markdown: str) -> dict:
    """Extract sections from the paper markdown."""
    sections = {}
    
    # Pattern to match section headers (## 1. Section Name or ## Section Name)
    section_pattern = r'^##\s*(?:\d+\.)?\s*(.+?)$'
    
    lines = paper_markdown.split('\n')
    current_section = None
    current_content = []
    
    for line in lines:
        match = re.match(section_pattern, line.strip())
        if match:
            # Save previous section
            if current_section:
                sections[current_section] = '\n'.join(current_content).strip()
            
            # Start new section
            current_section = match.group(1).strip().lower().replace(' ', '_')
            current_content = []
        elif current_section:
            current_content.append(line)
    
    # Save last section
    if current_section:
        sections[current_section] = '\n'.join(current_content).strip()
    
    return sections


def reassemble_paper(title: str, sections: dict) -> str:
    """Reassemble the paper from sections."""
    section_order = [
        ("abstract", "Abstract"),
        ("introduction", "1. Introduction"),
        ("related_work", "2. Related Work"),
        ("method", "3. Method"),
        ("experiments", "4. Experiments"),
        ("discussion", "5. Discussion"),
        ("conclusion", "6. Conclusion"),
        ("references", "References"),
    ]
    
    paper = f"# {title}\n\n"
    
    for section_key, section_title in section_order:
        content = sections.get(section_key, "")
        if content:
            paper += f"## {section_title}\n\n{content}\n\n---\n\n"
    
    return paper
