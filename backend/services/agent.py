import openai
from openai import AsyncOpenAI
import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from services.edgar_service import edgar_service
from redis_client import redis_client
from routers.market.equity.stocks import get_micro_data

# Configure logging
logger = logging.getLogger(__name__)

class AgentService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        self.CACHE_TTL_SECONDS = 24 * 60 * 60  # 24 hours

    def _ensure_client(self):
        """Ensure AsyncOpenAI client is initialized."""
        if not self.client:
            if not self.api_key:
                 # Try to reload from env
                self.api_key = os.getenv("OPENAI_API_KEY")
                
            if self.api_key:
                try:
                    self.client = AsyncOpenAI(api_key=self.api_key)
                except Exception as e:
                    logger.error(f"Failed to initialize AsyncOpenAI client: {e}")
                    raise ValueError(f"Failed to initialize AsyncOpenAI client: {e}")
            else:
                raise ValueError("OPENAI_API_KEY not configured. Please set OPENAI_API_KEY environment variable.")
        return self.client



    async def generate_report(self, data_context: str, prompt_customization: str = ""):
        """
        Generate a report based on the provided data context.
        """
        try:
            client = self._ensure_client()
            response = await client.chat.completions.create(
                model="gpt-4o", 
                messages=[
                    {"role": "system", "content": "You are a financial analyst agent. Generate a comprehensive report based on the provided data."},
                    {"role": "user", "content": f"Data Context:\n{data_context}\n\nCustom Instructions:\n{prompt_customization}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise Exception(f"Error generating report: {str(e)}")



agent_service = AgentService()
