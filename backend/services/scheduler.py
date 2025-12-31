from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from redis_client import redis_client
from services.market.indices import fetch_regional_indices_data, fetch_major_indices_data
from services.market.crypto import fetch_crypto_data
from services.market.currency import fetch_currency_data
from services.market.commodity import fetch_commodity_data
from services.market.economic import fetch_all_economic_data
from services.ai_report import generate_market_report
import asyncio
import json

scheduler = AsyncIOScheduler()

async def update_regional_indices():
    # print("Scheduler: Updating regional indices...")
    try:
        data = await fetch_regional_indices_data()
        if data:
            # Cache key matches what router expects
            redis_client.set_cache("indices:regional:all:v2", data, ttl=3600)  # 1 hour TTL in case scheduler dies
            # Publish update
            redis_client.publish('market_updates', json.dumps({'type': 'indices_regional', 'data': data}))
            # print("Scheduler: Regional indices updated.")
    except Exception as e:
        print(f"Scheduler Error (Regional Indices): {e}")

async def update_major_indices():
    # print("Scheduler: Updating major indices...")
    try:
        data = await fetch_major_indices_data()
        if data:
            redis_client.set_cache("indices:data", data, ttl=3600)
            redis_client.publish('market_updates', json.dumps({'type': 'indices_major', 'data': data}))
            # print("Scheduler: Major indices updated.")
    except Exception as e:
        print(f"Scheduler Error (Major Indices): {e}")

async def update_crypto_data():
    # print("Scheduler: Updating crypto data...")
    try:
        # Default to daily timeframe for the dashboard fast view
        data = await fetch_crypto_data(timeframe="daily")
        if data:
            # Cache key matches router
            redis_client.set_cache("crypto:all:daily", data, ttl=900)
            redis_client.publish('market_updates', json.dumps({'type': 'crypto_all', 'data': data}))
            # print("Scheduler: Crypto data updated.")
    except Exception as e:
        print(f"Scheduler Error (Crypto): {e}")

async def update_currency_data():
    # print("Scheduler: Updating currency data...")
    try:
        # Fetching 'monthly' (1 year) data as default for the main dashboard view
        data = await fetch_currency_data(timeframe="monthly")
        if data:
            redis_client.set_cache("currency:data:monthly", data, ttl=3600)
            redis_client.publish('market_updates', json.dumps({'type': 'currency_update', 'data': data}))
            # print("Scheduler: Currency data updated.")
    except Exception as e:
        print(f"Scheduler Error (Currency): {e}")

async def update_commodity_data():
    print("Scheduler: Updating commodity data...")
    try:
        # Default to monthly (1y) for dashboard charts
        data = await fetch_commodity_data(timeframe="monthly")
        if data:
            redis_client.set_cache("commodity:data:monthly", data, ttl=3600)
            redis_client.publish('market_updates', json.dumps({'type': 'commodity_update', 'data': data}))
            print("Scheduler: Commodity data updated.")
    except Exception as e:
        print(f"Scheduler Error (Commodity): {e}")

async def update_economic_data():
    # print("Scheduler: Updating economic data...")
    try:
        # Default to monthly (1y) for dashboard charts
        data = await fetch_all_economic_data(timeframe="monthly")
        if data:
            redis_client.set_cache("macro:monthly", data, ttl=14400)  # 4 hour TTL
            redis_client.publish('market_updates', json.dumps({'type': 'economic_update', 'data': data}))
            # print("Scheduler: Economic data updated.")
    except Exception as e:
        print(f"Scheduler Error (Economic): {e}")

async def scheduled_market_report():
    try:
        config = redis_client.get_cache("ai_report:config")
        if config and config.get("enabled"):
            print("Scheduler: Starting scheduled AI Market Report...")
            await generate_market_report()
            print("Scheduler: Scheduled AI Market Report completed.")
    except Exception as e:
        print(f"Scheduler Error (AI Report): {e}")

def start_scheduler():
    # Schedule jobs
    scheduler.add_job(
        update_regional_indices,
        trigger=IntervalTrigger(seconds=300), # 5 mins
        id='update_regional_indices',
        replace_existing=True
    )
    
    scheduler.add_job(
        update_major_indices,
        trigger=IntervalTrigger(seconds=60),
        id='update_major_indices',
        replace_existing=True
    )
    
    scheduler.add_job(
        update_crypto_data,
        trigger=IntervalTrigger(seconds=60), # 1 min
        id='update_crypto_data',
        replace_existing=True
    )
    
    scheduler.add_job(
        update_currency_data,
        trigger=IntervalTrigger(seconds=60), # 1 min
        id='update_currency_data',
        replace_existing=True
    )
    
    scheduler.add_job(
        update_commodity_data,
        trigger=IntervalTrigger(seconds=60), # 1 min
        id='update_commodity_data',
        replace_existing=True
    )
    
    scheduler.add_job(
        update_economic_data,
        trigger=IntervalTrigger(seconds=300), # 5 mins - economic data updates less frequently
        id='update_economic_data',
        replace_existing=True
    )

    scheduler.add_job(
        scheduled_market_report,
        trigger=CronTrigger(day_of_week='mon-fri', hour=9, minute=20),
        id='ai_market_report',
        replace_existing=True
    )
    
    scheduler.start()
    print("Market Data Scheduler started.")

async def run_initial_fetch():
    """Run fetch immediately on startup so we don't wait 60s"""
    await update_regional_indices()
    await update_major_indices()
    await update_crypto_data()
    await update_currency_data()
    await update_commodity_data()
    await update_economic_data()
