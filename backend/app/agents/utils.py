import json
import re
import logging
from json_repair import repair_json

logger = logging.getLogger(__name__)

def parse_json(content: str) -> dict:
    """
    Robustly parse JSON from LLM output using json-repair.
    Handles common LLM mistakes like:
    - Missing commas
    - Single quotes
    - Invalid escapes (e.g. \alpha)
    - Unescaped newlines within strings
    - Leading/trailing text
    """
    if not content:
        return {}
        
    # Pre-cleaning: Extract content within markdown blocks if present
    # This helps json-repair focus on the actual JSON segment
    json_str = content.strip()
    
    if "```json" in json_str:
        json_str = json_str.split("```json")[1].split("```")[0]
    elif "```" in json_str:
        # Try to find the first { and last } if it's just in a generic code block
        start = json_str.find('{')
        end = json_str.rfind('}')
        if start != -1 and end != -1:
            json_str = json_str[start:end+1]
        else:
            # Fallback to splitting if no braces found
            json_str = json_str.split("```")[1].split("```")[0]
    else:
        # No markdown block, find first { and last }
        start = json_str.find('{')
        end = json_str.rfind('}')
        if start != -1 and end != -1:
            json_str = json_str[start:end+1]

    json_str = json_str.strip()
    
    try:
        # Step 1: Try standard JSON parse
        return json.loads(json_str)
    except json.JSONDecodeError:
        try:
            # Step 2: Use json-repair to fix common issues
            repaired = repair_json(json_str)
            return json.loads(repaired)
        except Exception as e:
            logger.error(f"JSON repair failed. Summary: {str(e)[:100]}")
            # Step 3: Minimal regex repair as last resort (for specific escape issues)
            try:
                # Fix backslashes that aren't valid escapes
                fixed = re.sub(r'\\(?!(["\\/bfnrt]|u[0-9a-fA-F]{4}))', r'\\\\', json_str)
                return json.loads(repair_json(fixed))
            except Exception:
                logger.error(f"Ultimate JSON failure. Raw content preview: {json_str[:200]}...")
                # Still raise the original repair exception or a descriptive one
                raise ValueError(f"Failed to parse or repair JSON from LLM: {str(e)}")
