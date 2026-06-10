"""
batch_handler.py
OpenAI Batch API handler: chunking, submission, polling, checkpointing.
"""

import json
import sys
import time
from typing import List, Dict, Any, Tuple
from openai import OpenAI
from prompt import build_extraction_prompt


class BatchHandler:
    """Handle batching and OpenAI Batch API interactions."""
    
    def __init__(self, api_key: str, batch_size: int = 45):
        self.client = OpenAI(api_key=api_key)
        self.batch_size = batch_size
    
    def create_chunks(self, reviews: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Split reviews into chunks of batch_size."""
        chunks = []
        for i in range(0, len(reviews), self.batch_size):
            chunks.append(reviews[i:i + self.batch_size])
        return chunks
    
    def submit_batch(self, chunk: List[Dict[str, Any]]) -> str:
        """
        Submit a batch of reviews to OpenAI Batch API.
        
        Returns batch_id.
        """
        # Build batch requests
        requests = []
        for idx, review in enumerate(chunk, start=1):
            prompt = build_extraction_prompt(review["text_clean"])
            
            requests.append({
                "custom_id": review["review_id"],
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0,
                }
            })
        
        # Convert to JSONL format (one request per line)
        jsonl_content = "\n".join([json.dumps(r) for r in requests])
        
        # Submit batch
        batch_file = self.client.files.create(
            file=("batch.jsonl", jsonl_content, "application/octet-stream"),
        )
        
        batch = self.client.beta.batches.create(
            input_file_id=batch_file.id,
            endpoint="/v1/chat/completions",
            timeout_minutes=60,
        )
        
        log_event("batch_submitted", {
            "batch_id": batch.id,
            "review_count": len(chunk),
            "file_id": batch_file.id,
        })
        
        return batch.id
    
    def poll_batch(self, batch_id: str, timeout_seconds: int = 3600) -> Dict[str, Any]:
        """
        Poll batch until completion or timeout.
        
        Returns batch object with results.
        """
        start_time = time.time()
        poll_interval = 10  # seconds
        
        while time.time() - start_time < timeout_seconds:
            batch = self.client.beta.batches.retrieve(batch_id)
            
            log_event("batch_polling", {
                "batch_id": batch_id,
                "status": batch.status,
                "processing_count": batch.request_counts.processing,
                "completed_count": batch.request_counts.completed,
                "failed_count": batch.request_counts.failed,
            })
            
            if batch.status == "completed":
                log_event("batch_completed", {"batch_id": batch_id})
                return batch
            
            if batch.status == "failed":
                raise RuntimeError(f"Batch {batch_id} failed: {batch.errors}")
            
            # Wait before polling again
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Batch {batch_id} did not complete within {timeout_seconds}s")
    
    def retrieve_results(self, batch: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Retrieve and parse results from completed batch.
        
        Returns list of results with format:
        {
            "review_id": "...",
            "status": "succeeded|failed",
            "response": {...},  # parsed LLM response if succeeded
            "error": "..."      # error message if failed
        }
        """
        results = []
        
        # Retrieve output file
        output_file = self.client.files.content(batch.output_file_id)
        output_lines = output_file.text.strip().split("\n")
        
        for line in output_lines:
            result_obj = json.loads(line)
            
            review_id = result_obj["custom_id"]
            
            if result_obj["result"]["status"] == "succeeded":
                # Extract LLM response
                llm_response = result_obj["result"]["message"]["content"]
                
                results.append({
                    "review_id": review_id,
                    "status": "succeeded",
                    "response": llm_response,
                })
            else:
                # API error
                error_msg = result_obj["result"].get("error", {}).get("message", "Unknown error")
                
                results.append({
                    "review_id": review_id,
                    "status": "failed",
                    "error": error_msg,
                })
        
        return results


def log_event(event: str, details: Dict[str, Any] = None) -> None:
    """Log event to stderr in JSON format."""
    log_entry = {
        "event": event,
        **(details or {})
    }
    print(json.dumps(log_entry), file=sys.stderr)
