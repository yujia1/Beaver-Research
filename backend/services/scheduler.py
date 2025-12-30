from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from redis_client import redis_client
from services.market.indices import fetch_regional_indices_data, fetch_major_indices_data
import asyncio
import json

scheduler = AsyncIOScheduler()

async def update_regional_indices():
    print("Scheduler: Updating regional indices...")
    try:
        data = await fetch_regional_indices_data()
        if data:
            # Cache key matches what router expects
            redis_client.set_cache("indices:regional:all:v2", data, ttl=3600)  # 1 hour TTL in case scheduler dies
            # Publish update
            redis_client.publish('market_updates', json.dumps({'type': 'indices_regional', 'data': data}))
            print("Scheduler: Regional indices updated.")
    except Exception as e:
        print(f"Scheduler Error (Regional Indices): {e}")

async def update_major_indices():
    print("Scheduler: Updating major indices...")
    try:
        data = await fetch_major_indices_data()
        if data:
            redis_client.set_cache("indices:data", data, ttl=3600)
            redis_client.publish('market_updates', json.dumps({'type': 'indices_major', 'data': data}))
            print("Scheduler: Major indices updated.")
    except Exception as e:
        print(f"Scheduler Error (Major Indices): {e}")

def start_scheduler():
    # Schedule jobs
    scheduler.add_job(
        update_regional_indices,
        trigger=IntervalTrigger(seconds=300), # 5 mins: Balances freshness with FMP Bandwidth limits (20GB/mo)
        id='update_regional_indices',
        replace_existing=True
    )
    
    scheduler.add_job(
        update_major_indices,
        trigger=IntervalTrigger(seconds=60),
        id='update_major_indices',
        replace_existing=True
    )
    
    scheduler.start()
    print("Market Data Scheduler started.")

async def run_initial_fetch():
    """Run fetch immediately on startup so we don't wait 60s"""
    await update_regional_indices()
    await update_major_indices()
