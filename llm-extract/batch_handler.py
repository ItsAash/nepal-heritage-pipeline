"""
batch_handler.py
OpenAI Batch API handler: chunking, submission, polling, checkpointing.
"""

from io import BytesIO
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
            file=BytesIO(jsonl_content.encode("utf-8")),
            purpose="batch"
        )
        
        batch = self.client.batches.create(
            input_file_id=batch_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h"
        )
        
        log_event("batch_submitted", {
            "batch_id": batch.id,
            "review_count": len(chunk),
            "file_id": batch_file.id,
        })
        
        return batch.id
    
    def poll_batch(self, batch_id: str, timeout_seconds: int = 3600):
        """
        Poll batch until completion or timeout.
        
        Returns batch object with results.
        """
        start_time = time.time()
        poll_interval = 10  # seconds
        
        while time.time() - start_time < timeout_seconds:
            batch = self.client.batches.retrieve(batch_id)

            # Debug SDK response shape during development
            if hasattr(batch, "request_counts"):
                try:
                    log_event("batch_request_counts_shape", {
                        "fields": list(batch.request_counts.model_dump().keys())
                    })
                except Exception:
                    pass

            request_counts = getattr(batch, "request_counts", None)

            log_event("batch_polling", {
                "batch_id": batch_id,
                "status": batch.status,
                "request_counts": request_counts.model_dump() if hasattr(request_counts, "model_dump") else str(request_counts),
            })
            
            if batch.status == "completed":
                log_event("batch_completed", {"batch_id": batch_id})
                return batch
            
            if batch.status in {"failed", "expired", "cancelled"}:
                raise RuntimeError(
                    f"Batch {batch_id} ended with status={batch.status}: {getattr(batch, 'errors', None)}"
                )
            
            # Wait before polling again
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Batch {batch_id} did not complete within {timeout_seconds}s")
    
    def retrieve_results(self, batch) -> List[Dict[str, Any]]:
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
        content = self.client.files.content(batch.output_file_id)

        if hasattr(content, "text"):
            raw_text = content.text
        elif hasattr(content, "read"):
            raw_text = content.read().decode("utf-8")
        else:
            raw_text = str(content)

        output_lines = raw_text.strip().split("\n")
        
        for line in output_lines:
            if not line.strip():
                continue

            result_obj = json.loads(line)

            review_id = result_obj["custom_id"]

            response_body = result_obj.get("response", {}).get("body", {})
            error_obj = result_obj.get("error")

            if error_obj is None:
                try:
                    llm_response = response_body["choices"][0]["message"]["content"]

                    results.append({
                        "review_id": review_id,
                        "status": "succeeded",
                        "response": llm_response,
                    })
                except Exception as exc:
                    results.append({
                        "review_id": review_id,
                        "status": "failed",
                        "error": f"Response parsing failed: {exc}",
                    })
            else:
                results.append({
                    "review_id": review_id,
                    "status": "failed",
                    "error": str(error_obj),
                })
        
        return results


def log_event(event: str, details: Dict[str, Any] = None) -> None:
    """Log event to stderr in JSON format."""
    log_entry = {
        "event": event,
        **(details or {})
    }
    print(json.dumps(log_entry), file=sys.stderr)
