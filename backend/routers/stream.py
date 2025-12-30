from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import redis.asyncio as redis
import os
import asyncio
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Redis Configuration (Same as redis_client.py)
REDIS_HOST = os.getenv("REDISHOST", os.getenv("REDIS_HOST", "localhost"))
REDIS_PORT = int(os.getenv("REDISPORT", os.getenv("REDIS_PORT", "6379")))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDISPASSWORD", os.getenv("REDIS_PASSWORD", None))

@router.get("/market")
async def stream_market_data():
    """
    Server-Sent Events (SSE) endpoint for real-time market data updates.
    """
    # Create a dedicated async client for this connection
    client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True
    )
    
    async def event_generator():
        pubsub = client.pubsub()
        await pubsub.subscribe('market_updates')
        
        try:
            # Send initial ping or data to confirm connection
            # yield "event: connected\ndata: {\"status\":\"connected\"}\n\n"
            
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    # Parse data to ensure it's valid JSON (it should be)
                    payload = message['data']
                    # Yield in SSE format
                    yield f"data: {payload}\n\n"
        except asyncio.CancelledError:
            print("Client disconnected from stream")
        except Exception as e:
            logger.error(f"Stream error: {e}")
        finally:
            await pubsub.unsubscribe('market_updates')
            await client.close()
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")
