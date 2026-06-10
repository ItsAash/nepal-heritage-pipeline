"""
config.py
Simple environment variable management for llm-extract job.
Loads from .env file and system environment variables.
"""

import os
from typing import Optional
import dotenv


class Config:
    """Load and validate configuration from .env file and environment variables."""
    
    def __init__(self):
        # Load environment variables from .env file
        dotenv.load_dotenv()
        
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.SUPABASE_URL = os.getenv("SUPABASE_URL")
        self.SUPABASE_KEY = os.getenv("SUPABASE_KEY")
        self.MAX_REVIEWS_PER_RUN = int(os.getenv("MAX_REVIEWS_PER_RUN", "1000000"))

        # Constants
        self.OPENAI_MODEL = "gpt-4o-mini"
        self.BATCH_SIZE = 45  # Reviews per batch submission
        self.TIMEOUT_SECONDS = 3600  # Max wait for batch completion
    
    def validate(self) -> None:
        """Validate all required environment variables."""
        missing = []
        # print(self.OPENAI_API_KEY, self.SUPABASE_URL, self.SUPABASE_KEY)
        if not self.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        if not self.SUPABASE_URL:
            missing.append("SUPABASE_URL")
        if not self.SUPABASE_KEY:
            missing.append("SUPABASE_KEY")
        
        if missing:
            raise ValueError(f"Missing required env vars: {', '.join(missing)}")
    
    def summary(self) -> dict:
        """Return config summary (safe to log)."""
        return {
            "openai_model": self.OPENAI_MODEL,
            "batch_size": self.BATCH_SIZE,
            "max_reviews_per_run": self.MAX_REVIEWS_PER_RUN,
            "timeout_seconds": self.TIMEOUT_SECONDS,
        }
