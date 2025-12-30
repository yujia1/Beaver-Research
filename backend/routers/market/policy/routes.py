from fastapi import APIRouter, HTTPException
import requests
import json
import datetime
import yfinance as yf
import random

router = APIRouter()

@router.get("/polymarket/{ticker}")
async def get_polymarket_data(ticker: str):
    """
    Fetch PolyMarket prediction market data for a given ticker using Gamma API.
    Returns odds/probabilities for various price targets.
    """
    try:
        # Get current stock price from yfinance for context
        base_price = 200.0
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            if info and 'currentPrice' in info:
                base_price = float(info.get('currentPrice', 200.0))
        except Exception as e:
            print(f"Warning: Could not fetch current price for {ticker}: {e}")
        
        # PolyMarket Gamma API base URL
        gamma_api_base = "https://gamma-api.polymarket.com"
        
        # Prepare basic headers
        headers = {
            'User-Agent': 'Financial Dashboard/1.0',
            'Accept': 'application/json'
        }
        
        print(f"[POLYMARKET] Using Gamma API (public) for market data")
        
        # Search for markets related to the ticker
        search_queries = [
            ticker.upper(),
            f"{ticker.upper()} stock",
            f"{ticker.upper()} price",
            f"{ticker.upper()} hit"
        ]
        
        all_markets = []
        
        # Try /markets endpoint first
        try:
            markets_url = f"{gamma_api_base}/markets"
            params = {
                "limit": 100,
                "active": "true"
            }
            
            print(f"[POLYMARKET] Fetching markets from {markets_url}")
            response = requests.get(markets_url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                markets_data = response.json()
                
                markets_list = []
                if isinstance(markets_data, list):
                    markets_list = markets_data
                elif isinstance(markets_data, dict):
                    markets_list = markets_data.get('markets', markets_data.get('data', markets_data.get('results', [])))
                
                ticker_lower = ticker.lower()
                ticker_upper = ticker.upper()
                for market in markets_list:
                    if not isinstance(market, dict):
                        continue
                    question = (market.get('question', '') or market.get('title', '') or market.get('name', '') or '').lower()
                    if ticker_lower in question or ticker_upper in question:
                        if any(kw in question for kw in ['price', 'hit', '$', 'reach', 'above', 'below', 'stock']):
                            all_markets.append(market)
        except Exception as e:
            print(f"[POLYMARKET] Error fetching from /markets endpoint: {e}")
        
        # If no markets found, try /search endpoint as fallback
        if not all_markets:
            for query in search_queries:
                try:
                    search_url = f"{gamma_api_base}/search"
                    params = {
                        "q": query,
                        "limit": 50
                    }
                    
                    response = requests.get(search_url, params=params, headers=headers, timeout=10)
                    if response.status_code != 200:
                        continue

                    search_results = response.json()
                    
                    if isinstance(search_results, list):
                        for item in search_results:
                            if isinstance(item, dict):
                                if 'markets' in item and isinstance(item['markets'], list):
                                    all_markets.extend(item['markets'])
                                elif 'question' in item or 'title' in item:
                                    all_markets.append(item)
                                else:
                                    all_markets.append(item)
                except Exception:
                    continue
                
        # Filter markets that are related to stock price predictions
        relevant_markets = []
        ticker_lower = ticker.lower()
        ticker_upper = ticker.upper()
        
        for market in all_markets:
            if not isinstance(market, dict):
                continue
            
            question = (market.get('question', '') or market.get('title', '') or market.get('name', '') or '').lower()
            title = (market.get('title', '') or market.get('name', '') or '').lower()
            description = (market.get('description', '') or market.get('subtitle', '') or '').lower()
            slug = (market.get('slug', '') or market.get('id', '') or '').lower()
            
            ticker_found = (ticker_lower in question or ticker_upper in question or 
                          ticker_lower in title or ticker_upper in title or
                          ticker_lower in description or ticker_upper in description or
                          ticker_lower in slug or ticker_upper in slug)
            
            price_keywords = ['price', 'hit', 'reach', 'above', 'below', '$', 'stock', 'share', 'trading']
            has_price_keyword = any(keyword in question or keyword in title or keyword in description or keyword in slug 
                                   for keyword in price_keywords)
            
            if ticker_found and has_price_keyword:
                relevant_markets.append(market)
        
        targets = []
        question_text = f"What will {ticker.upper()} hit before 2026?"
        is_real_data = False
        
        if relevant_markets:
            market = relevant_markets[0]
            question_text = market.get('question') or market.get('title') or market.get('name') or question_text
            
            outcomes = market.get('outcomes', [])
            if not outcomes: outcomes = market.get('tokens', [])
            if not outcomes: outcomes = market.get('conditions', [])
            if not outcomes and 'outcomePrices' in market: outcomes = market.get('outcomePrices', [])
            
            for outcome in outcomes:
                if not isinstance(outcome, dict): continue
                
                outcome_name = outcome.get('name', '') or outcome.get('title', '') or outcome.get('outcome', '')
                price = outcome.get('price', None) or outcome.get('lastPrice', None) or outcome.get('currentPrice', None)
                
                if price is None:
                    price_info = outcome.get('priceInfo', {})
                    if isinstance(price_info, dict):
                        price = price_info.get('price') or price_info.get('lastPrice')
                
                if price is not None:
                    try:
                        price_float = float(price)
                        odds_percent = round(price_float * 100, 1)
                        if outcome_name:
                            targets.append({
                                "target": outcome_name,
                                "odds": odds_percent
                            })
                    except (ValueError, TypeError):
                        continue
            
            is_real_data = len(targets) > 0
        
        # Fallback Mock Data if no targets
        if not targets:
            if base_price < 100:
                targets = [
                    {"target": f"${base_price * 1.2:.0f}+", "odds": round(random.uniform(35, 50), 1)},
                    {"target": f"${base_price * 1.5:.0f}+", "odds": round(random.uniform(20, 35), 1)},
                    {"target": f"${base_price * 2.0:.0f}+", "odds": round(random.uniform(10, 25), 1)},
                    {"target": f"${base_price * 2.5:.0f}+", "odds": round(random.uniform(5, 15), 1)},
                    {"target": f"${base_price * 3.0:.0f}+", "odds": round(random.uniform(2, 10), 1)}
                ]
            elif base_price < 300:
                targets = [
                    {"target": f"${base_price * 1.15:.0f}+", "odds": round(random.uniform(40, 55), 1)},
                    {"target": f"${base_price * 1.3:.0f}+", "odds": round(random.uniform(25, 40), 1)},
                    {"target": f"${base_price * 1.5:.0f}+", "odds": round(random.uniform(15, 30), 1)},
                    {"target": f"${base_price * 2.0:.0f}+", "odds": round(random.uniform(8, 20), 1)},
                    {"target": f"${base_price * 2.5:.0f}+", "odds": round(random.uniform(3, 12), 1)}
                ]
            else:
                targets = [
                    {"target": f"${base_price * 1.1:.0f}+", "odds": round(random.uniform(45, 60), 1)},
                    {"target": f"${base_price * 1.2:.0f}+", "odds": round(random.uniform(30, 45), 1)},
                    {"target": f"${base_price * 1.3:.0f}+", "odds": round(random.uniform(20, 35), 1)},
                    {"target": f"${base_price * 1.5:.0f}+", "odds": round(random.uniform(10, 25), 1)},
                    {"target": f"${base_price * 2.0:.0f}+", "odds": round(random.uniform(5, 15), 1)}
                ]
        
        def extract_price(target_str):
            try:
                cleaned = target_str.replace('$', '').replace('+', '').strip()
                return float(cleaned)
            except:
                return 0
        
        targets.sort(key=lambda x: extract_price(x["target"]))
        
        return {
            "ticker": ticker.upper(),
            "current_price": base_price,
            "question": question_text,
            "targets": targets,
            "is_real_data": is_real_data,
            "last_updated": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error fetching PolyMarket data for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
