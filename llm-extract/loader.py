"""
loader.py
Incremental loading with checkpoint recovery to Supabase.
"""

import json
import sys
from typing import List, Dict, Any
from supabase import create_client


class DataLoader:
    """Load transformed data into Supabase with checkpoint tracking."""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase = create_client(supabase_url, supabase_key)
    
    def load_entities(self, entities: List[Dict[str, Any]]) -> int:
        """
        Load entity records to entities_raw table.
        
        Returns count of inserted rows.
        """
        if not entities:
            return 0
        
        try:
            response = self.supabase.table("entities_raw").insert(entities).execute()
            count = len(response.data) if response.data else len(entities)
            
            log_event("entities_loaded", {
                "count": count,
                "review_count": len(set(e["review_id"] for e in entities)),
            })
            
            return count
        except Exception as e:
            log_event("entities_load_failed", {"error": str(e)}, level="ERROR")
            raise
    
    def load_relations(self, relations: List[Dict[str, Any]]) -> int:
        """
        Load relation records to relations_raw table.
        
        Returns count of inserted rows.
        """
        if not relations:
            return 0
        
        try:
            response = self.supabase.table("relations_raw").insert(relations).execute()
            count = len(response.data) if response.data else len(relations)
            
            log_event("relations_loaded", {
                "count": count,
                "review_count": len(set(r["review_id"] for r in relations)),
            })
            
            return count
        except Exception as e:
            log_event("relations_load_failed", {"error": str(e)}, level="ERROR")
            raise
    
    def load_sentiments(self, sentiments: List[Dict[str, Any]]) -> int:
        """
        Load sentiment records to sentiments_raw table.
        
        Returns count of inserted rows.
        """
        if not sentiments:
            return 0
        
        try:
            response = self.supabase.table("sentiments_raw").insert(sentiments).execute()
            count = len(response.data) if response.data else len(sentiments)
            
            log_event("sentiments_loaded", {
                "count": count,
                "review_count": len(set(s["review_id"] for s in sentiments)),
            })
            
            return count
        except Exception as e:
            log_event("sentiments_load_failed", {"error": str(e)}, level="ERROR")
            raise
    
    def mark_processed(self, review_id: str) -> None:
        """Mark review as processed in checkpoint table."""
        try:
            self.supabase.rpc("update_checkpoint", {
                "p_review_id": review_id,
                "p_status": "processed",
                "p_error_msg": None,
            }).execute()
        except Exception as e:
            log_event("checkpoint_update_failed", {
                "review_id": review_id,
                "error": str(e),
            }, level="ERROR")
            raise
    
    def mark_failed(self, review_id: str, error_msg: str) -> None:
        """Mark review as failed in checkpoint table."""
        try:
            self.supabase.rpc("update_checkpoint", {
                "p_review_id": review_id,
                "p_status": "failed",
                "p_error_msg": error_msg[:500],  # Truncate long errors
            }).execute()
        except Exception as e:
            log_event("checkpoint_update_failed", {
                "review_id": review_id,
                "error": str(e),
            }, level="ERROR")
            raise
    
    def get_unprocessed_reviews(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get unprocessed reviews from cleaned_reviews.
        
        Queries cleaned_reviews table, filters out already-processed reviews
        using checkpoint table.
        """
        try:
            response = self.supabase.rpc("get_unprocessed_reviews", {
                "limit_count": limit
            }).execute()
            
            reviews = response.data
            
            log_event("unprocessed_reviews_fetched", {
                "count": len(reviews),
            })
            
            return reviews
        except Exception as e:
            log_event("fetch_reviews_failed", {"error": str(e)}, level="ERROR")
            raise


def log_event(event: str, details: Dict[str, Any] = None, level: str = "INFO") -> None:
    """Log event to stderr in JSON format."""
    log_entry = {
        "event": event,
        "level": level,
        **(details or {})
    }
    print(json.dumps(log_entry), file=sys.stderr)
