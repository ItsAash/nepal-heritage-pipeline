"""
main.py
Gold Layer extraction pipeline orchestration.

Pipeline:
  1. Fetch unprocessed reviews from cleaned_reviews
  2. Create chunks
  3. Submit to OpenAI Batch API
  4. Poll for completion
  5. Parse & recover JSON
  6. Transform to 3 raw tables
  7. Load to Supabase
  8. Update checkpoints
"""

import sys
import json
from config import Config
from batch_handler import BatchHandler, log_event
from transformer import transform_extraction
from loader import DataLoader


def main():
    """Run extraction pipeline."""
    
    # Initialize
    config = Config()
    config.validate()
    
    # log_event("pipeline_start", config.summary())
    
    loader = DataLoader(config.SUPABASE_URL, config.SUPABASE_KEY)

    print("TEST: Sample Data Structure")
    print(loader.get_unprocessed_reviews(1))  # Fetch one review to see structure

    # batch_handler = BatchHandler(config.OPENAI_API_KEY, config.BATCH_SIZE)
    
    # try:
    #     # Step 1: Fetch unprocessed reviews
    #     log_event("fetching_reviews", {"limit": config.MAX_REVIEWS_PER_RUN})
    #     reviews = loader.get_unprocessed_reviews(config.MAX_REVIEWS_PER_RUN)
        
    #     if not reviews:
    #         log_event("no_reviews_to_process")
    #         return
        
    #     log_event("reviews_fetched", {"count": len(reviews)})
        
    #     # Step 2: Create chunks
    #     chunks = batch_handler.create_chunks(reviews)
    #     log_event("chunks_created", {
    #         "chunk_count": len(chunks),
    #         "batch_size": config.BATCH_SIZE,
    #     })
        
    #     # Step 3-8: Process each chunk
    #     total_entities = 0
    #     total_relations = 0
    #     total_sentiments = 0
    #     total_processed = 0
    #     total_failed = 0
        
    #     for chunk_idx, chunk in enumerate(chunks, start=1):
    #         log_event("processing_chunk", {
    #             "chunk_index": chunk_idx,
    #             "total_chunks": len(chunks),
    #             "reviews_in_chunk": len(chunk),
    #         })
            
    #         # Step 3: Submit batch
    #         batch_id = batch_handler.submit_batch(chunk)
            
    #         # Step 4: Poll for completion
    #         batch = batch_handler.poll_batch(batch_id, timeout_seconds=config.TIMEOUT_SECONDS)
            
    #         # Step 5: Retrieve results
    #         results = batch_handler.retrieve_results(batch)
            
    #         # Step 6-8: Transform and load each result
    #         for result in results:
    #             review_id = result["review_id"]
                
    #             # Find review metadata
    #             review = next((r for r in chunk if r["review_id"] == review_id), None)
    #             if not review:
    #                 log_event("review_metadata_not_found", {"review_id": review_id}, level="ERROR")
    #                 continue
                
    #             if result["status"] == "failed":
    #                 # API error
    #                 error_msg = result.get("error", "Unknown API error")
    #                 loader.mark_failed(review_id, error_msg)
    #                 total_failed += 1
                    
    #                 log_event("review_extraction_failed", {
    #                     "review_id": review_id,
    #                     "error": error_msg,
    #                 })
    #                 continue
                
    #             # Step 6: Transform
    #             llm_response = result["response"]
    #             entities, relations, sentiments, error_msg = transform_extraction(
    #                 review_id,
    #                 llm_response,
    #                 {
    #                     "year": review.get("year"),
    #                     "period": review.get("period"),
    #                     "trip_type": review.get("trip_type"),
    #                     "rating": review.get("rating"),
    #                 }
    #             )
                
    #             if error_msg:
    #                 # JSON parse/transform failed
    #                 loader.mark_failed(review_id, error_msg)
    #                 total_failed += 1
                    
    #                 log_event("review_processing_failed", {
    #                     "review_id": review_id,
    #                     "error": error_msg,
    #                 })
    #                 continue
                
    #             # Step 7: Load to Supabase
    #             try:
    #                 if entities:
    #                     loader.load_entities(entities)
    #                     total_entities += len(entities)
                    
    #                 if relations:
    #                     loader.load_relations(relations)
    #                     total_relations += len(relations)
                    
    #                 if sentiments:
    #                     loader.load_sentiments(sentiments)
    #                     total_sentiments += len(sentiments)
                    
    #                 # Step 8: Mark as processed
    #                 loader.mark_processed(review_id)
    #                 total_processed += 1
                    
    #                 log_event("review_processed", {
    #                     "review_id": review_id,
    #                     "entities": len(entities),
    #                     "relations": len(relations),
    #                     "sentiments": len(sentiments),
    #                 })
                
    #             except Exception as e:
    #                 log_event("review_loading_failed", {
    #                     "review_id": review_id,
    #                     "error": str(e),
    #                 }, level="ERROR")
    #                 loader.mark_failed(review_id, str(e))
    #                 total_failed += 1
        
    #     # Summary
    #     log_event("pipeline_complete", {
    #         "total_reviews_processed": total_processed,
    #         "total_reviews_failed": total_failed,
    #         "total_entities": total_entities,
    #         "total_relations": total_relations,
    #         "total_sentiments": total_sentiments,
    #     })
    
    # except Exception as e:
    #     log_event("pipeline_error", {
    #         "error": str(e),
    #         "error_type": type(e).__name__,
    #     }, level="ERROR")
    #     raise


def log_event(event: str, details: dict = None, level: str = "INFO") -> None:
    """Log event to stderr in JSON format."""
    log_entry = {
        "event": event,
        "level": level,
        **(details or {})
    }
    print(json.dumps(log_entry), file=sys.stderr)


if __name__ == "__main__":
    main()
