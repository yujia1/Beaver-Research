from fastapi import APIRouter
import asyncio
import httpx
import xml.etree.ElementTree as ET
from datetime import datetime
from redis_client import redis_client
import re

router = APIRouter()

# Cache configuration
MARKET_NEWS_CACHE_KEY = "market_news_feed_v2"
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
        # Register namespaces to handle content:encoded
        namespaces = {
            'content': 'http://purl.org/rss/1.0/modules/content/',
            'dc': 'http://purl.org/dc/elements/1.1/'
        }
        
        root = ET.fromstring(content)
        
        for item in root.findall(".//item")[:15]:
            title_elem = item.find("title")
            link_elem = item.find("link")
            pub_date_elem = item.find("pubDate")
            description_elem = item.find("description")
            guid_elem = item.find("guid")
            
            # Try to find content:encoded
            content_encoded = item.find("content:encoded", namespaces)
            if content_encoded is None:
                 # Fallback: try searching with full braced name if namespace map fails 
                 content_encoded = item.find("{http://purl.org/rss/1.0/modules/content/}encoded")
            
            if title_elem is not None:
                # Basic cleaning of description for summary
                summary_text = ""
                if description_elem is not None and description_elem.text:
                    clean_desc = re.sub('<[^<]+?>', '', description_elem.text)
                    summary_text = clean_desc[:200] + "..." if len(clean_desc) > 200 else clean_desc
                
                # Content prioritization: content:encoded > description
                full_content = ""
                if content_encoded is not None and content_encoded.text:
                    full_content = content_encoded.text
                elif description_elem is not None and description_elem.text:
                    full_content = description_elem.text
                
                # Sentiment placeholder
                sentiment = "neutral" 
                
                items.append({
                    "id": guid_elem.text if guid_elem is not None else (link_elem.text if link_elem is not None else title_elem.text),
                    "headline": title_elem.text,
                    "summary": summary_text,
                    "content": full_content,
                    "link": link_elem.text if link_elem is not None else "",
                    "time": pub_date_elem.text if pub_date_elem is not None else "",
                    "tags": [config["tag"]],
                    "sentiment": sentiment
                })
                    
    except Exception as e:
        print(f"Error parsing feed: {e}")
        pass
        
    return items
