"""
transformer.py
Transform LLM JSON output into 3 raw tables (entities, relations, sentiments).
"""

import json
import sys
from typing import Dict, Any, Tuple, List
from json_recovery import recover_json


def transform_extraction(
    review_id: str,
    llm_response: str,
    review_metadata: Dict[str, Any]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """
    Transform LLM JSON response into 3 raw tables.
    
    Returns:
        (entities, relations, sentiments, error_msg)
        - entities: list of entity records
        - relations: list of relation records
        - sentiments: list of sentiment records
        - error_msg: None if success, error message if parse/transform failed
    """
    
    # Try to parse JSON
    try:
        data = json.loads(llm_response)
    except json.JSONDecodeError:
        # Try recovery techniques
        data = recover_json(llm_response)
        
        if data is None:
            error_msg = "Failed to parse JSON and all recovery techniques failed"
            log_event("json_parse_failed", {
                "review_id": review_id,
                "error": error_msg,
            })
            return [], [], [], error_msg
    
    # Extract metadata
    year = review_metadata.get("year")
    period = review_metadata.get("period")
    trip_type = review_metadata.get("trip_type")
    rating = review_metadata.get("rating")
    
    entities = []
    relations = []
    sentiments = []
    
    try:
        # Transform entities
        for entity in data.get("entities", []):
            entities.append({
                "review_id": review_id,
                "year": year,
                "period": period,
                "trip_type": trip_type,
                "entity_name": entity.get("name", ""),
                "entity_type": entity.get("type", ""),
                "quote": entity.get("quote", ""),
                "rating": rating,
            })
        
        # Transform relations
        for relation in data.get("relations", []):
            relations.append({
                "review_id": review_id,
                "year": year,
                "source_node": relation.get("from_id", ""),
                "target_node": relation.get("to_id", ""),
                "relation": relation.get("type", ""),
                "description": relation.get("description", ""),
            })
        
        # Transform sentiments
        for sentiment in data.get("aspect_sentiments", []):
            sentiments.append({
                "review_id": review_id,
                "year": year,
                "trip_type": trip_type,
                "aspect": sentiment.get("aspect", ""),
                "sentiment": sentiment.get("sentiment", ""),
                "score": sentiment.get("score", 0.5),
                "evidence": sentiment.get("evidence", ""),
                "rating": rating,
            })
        
        log_event("extraction_transformed", {
            "review_id": review_id,
            "entity_count": len(entities),
            "relation_count": len(relations),
            "sentiment_count": len(sentiments),
        })
        
        return entities, relations, sentiments, None
    
    except Exception as e:
        error_msg = f"Transformation failed: {str(e)}"
        log_event("transformation_error", {
            "review_id": review_id,
            "error": error_msg,
        })
        return [], [], [], error_msg


def log_event(event: str, details: Dict[str, Any] = None) -> None:
    """Log event to stderr in JSON format."""
    log_entry = {
        "event": event,
        **(details or {})
    }
    print(json.dumps(log_entry), file=sys.stderr)
