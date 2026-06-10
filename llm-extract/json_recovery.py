"""
json_recovery.py
Regex-based JSON recovery for malformed LLM responses.
"""

import re
import json
from typing import Optional, Dict, Any


def recover_json(response: str) -> Optional[Dict[str, Any]]:
    """
    Attempt to recover valid JSON from malformed response.
    
    Strategies:
    1. Try direct JSON parsing
    2. Extract JSON from markdown fences
    3. Use regex to rebuild JSON structure
    4. Return None if all fail
    """
    
    # Strategy 1: Direct JSON parsing
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Extract from markdown fences
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Strategy 3: Extract bare JSON object (without markdown)
    json_match = re.search(r"(\{[\s\S]*\})", response)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Strategy 4: Regex-based field extraction
    try:
        return _regex_recover_json(response)
    except Exception:
        pass
    
    # All strategies failed
    return None


def _regex_recover_json(response: str) -> Dict[str, Any]:
    """
    Use regex to extract and rebuild JSON structure from malformed response.
    
    Looks for patterns like:
    - "entities": [...] or "entities" : [...]
    - "relations": [...] or "relations" : [...]
    - etc.
    """
    
    result = {
        "entities": [],
        "relations": [],
        "aspect_sentiments": [],
        "review_type": "mixed",
        "dominant_experience": ""
    }
    
    # Extract entities array
    entities_match = re.search(
        r'"entities"\s*:\s*\[(.*?)\](?=\s*[,}])',
        response,
        re.DOTALL
    )
    if entities_match:
        result["entities"] = _parse_array_items(
            entities_match.group(1),
            ["id", "name", "type", "quote"]
        )
    
    # Extract relations array
    relations_match = re.search(
        r'"relations"\s*:\s*\[(.*?)\](?=\s*[,}])',
        response,
        re.DOTALL
    )
    if relations_match:
        result["relations"] = _parse_array_items(
            relations_match.group(1),
            ["from_id", "to_id", "type", "description"]
        )
    
    # Extract aspect_sentiments array
    sentiments_match = re.search(
        r'"aspect_sentiments"\s*:\s*\[(.*?)\](?=\s*[,}])',
        response,
        re.DOTALL
    )
    if sentiments_match:
        result["aspect_sentiments"] = _parse_array_items(
            sentiments_match.group(1),
            ["aspect", "sentiment", "score", "evidence"]
        )
    
    # Extract review_type
    type_match = re.search(r'"review_type"\s*:\s*"([^"]*)"', response)
    if type_match:
        result["review_type"] = type_match.group(1)
    
    # Extract dominant_experience
    exp_match = re.search(r'"dominant_experience"\s*:\s*"([^"]*)"', response)
    if exp_match:
        result["dominant_experience"] = exp_match.group(1)
    
    return result


def _parse_array_items(
    array_text: str,
    fields: list
) -> list:
    """Parse array of objects using regex."""
    
    items = []
    
    # Split by }, { to separate objects
    object_matches = re.findall(r"\{([^{}]+)\}", array_text)
    
    for obj_text in object_matches:
        obj = {}
        
        for field in fields:
            # Match field: value (handles both string and numeric values)
            pattern = f'"{field}"\\s*:\\s*(?:"([^"]*)")|(\\d+(?:\\.\\d+)?)'
            match = re.search(pattern, obj_text)
            
            if match:
                if match.group(1) is not None:
                    obj[field] = match.group(1)
                else:
                    # Try to parse as number
                    try:
                        obj[field] = float(match.group(2))
                        if obj[field].is_integer():
                            obj[field] = int(obj[field])
                    except (ValueError, AttributeError):
                        obj[field] = match.group(2)
        
        if obj:
            items.append(obj)
    
    return items
