
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
        # Cache for 5 minutes (longer than poll interval of 3 mins)
        redis_client.set_cache(MARKET_NEWS_CACHE_KEY, items, ttl=300)
        
    return items

async def background_news_fetcher():
    """Background task to fetch news every 3 minutes"""
    while True:
        try:
            items = await _fetch_market_news_from_source()
            if items:
                # Set TTL longer than sleep (5m TTL vs 3m Sleep) to ensure overlap
                redis_client.set_cache(MARKET_NEWS_CACHE_KEY, items, ttl=300)
        except Exception as e:
            print(f"Error in background news fetch: {e}")
        
        await asyncio.sleep(180) # Sleep 3 minutes

def start_news_polling():
    """Start the background polling task"""
    asyncio.create_task(background_news_fetcher())

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
            # Create tasks for all feeds
            tasks = [client.get(feed["url"]) for feed in feeds]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, response in enumerate(responses):
                feed_config = feeds[i]
                
                if isinstance(response, Exception):
                    print(f"Error fetching {feed_config['url']}: {response}")
                    continue
                    
                if response.status_code != 200:
                    print(f"Failed to fetch {feed_config['url']}: {response.status_code}")
                    continue
                
                # Parse the feed
                feed_items = _parse_feed_items(response.content, feed_config)
                items.extend(feed_items)
                
        # Sort items by date (newest first)
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
        print(f"Error in main fetch loop: {str(e)}")
        return []

def _parse_feed_items(content, config):
    """Parse RSS feed items"""
    items = []
    try:
        root = ET.fromstring(content)
        
        # Handle different feed types
        if config["type"] == "zerohedge":
            for item in root.findall(".//item")[:10]:  # Limit to 10 items
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
                    
        elif config["type"] == "bearcave":
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
        print(f"Error parsing feed {config['url']}: {e}")
        
    return items
