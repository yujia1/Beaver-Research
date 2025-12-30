from fastapi import APIRouter
import asyncio
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime
from redis_client import redis_client

router = APIRouter()

# Cache configuration
MARKET_NEWS_CACHE_KEY = "market_news_feed_v1"
MARKET_NEWS_CACHE_TTL = 180  # 3 minutes


@router.get("/market-news-feed")
async def get_market_news_feed():
    """Get market news feed from cache or fetch fresh"""
    # 1. Try Cache (Primary)
    cached_data = redis_client.get_cache(MARKET_NEWS_CACHE_KEY)
    if cached_data:
        return cached_data

    # 2. Fallback: Fetch immediately if cache is empty (e.g. first run)
    items = await _fetch_market_news_from_source()
    
    if items:
        # Cache for 5 minutes
        redis_client.set_cache(MARKET_NEWS_CACHE_KEY, items, ttl=300)
        
    return items


async def _fetch_market_news_from_source():
    """Fetch market news from RSS feeds"""
    items = []
    
    # Define feeds configuration
    feeds = [
        {"url": "http://feeds.feedburner.com/zerohedge/feed", "tag": "MARKETS", "type": "zerohedge"},
        {"url": "https://thebearcave.substack.com/feed", "tag": "RESEARCH", "type": "bearcave"}
    ]
    
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            tasks = [client.get(feed["url"]) for feed in feeds]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, response in enumerate(responses):
                feed_config = feeds[i]
                
                if isinstance(response, Exception):
                    continue
                    
                if response.status_code != 200:
                    continue
                
                feed_items = _parse_feed_items(response.content, feed_config)
                items.extend(feed_items)
                
        # Sort by date
        def parse_pub_date(date_str):
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(date_str)
                if dt: return dt
            except:
                pass
            return datetime.min.replace(tzinfo=None)

        items.sort(key=lambda x: parse_pub_date(x.get("time", "")), reverse=True)
        return items
            
    except Exception as e:
        return []


def _parse_feed_items(content, config):
    """Parse RSS feed items"""
    items = []
    try:
        root = ET.fromstring(content)
        
        for item in root.findall(".//item")[:10]:
            title_elem = item.find("title")
            link_elem = item.find("link")
            pub_date_elem = item.find("pubDate")
            
            if title_elem is not None and link_elem is not None:
                items.append({
                    "title": title_elem.text,
                    "link": link_elem.text,
                    "time": pub_date_elem.text if pub_date_elem is not None else "",
                    "tag": config["tag"]
                })
                    
    except Exception as e:
        pass
        
    return items
