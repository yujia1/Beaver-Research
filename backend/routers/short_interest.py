from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import time

router = APIRouter()

def parse_number(value: str) -> Optional[float]:
    """Parse a number string, handling K, M, B suffixes and removing %"""
    if not value or value == '-' or value.strip() == '':
        return None
    
    # Remove % sign
    value = value.replace('%', '').strip()
    
    # Handle empty or dash
    if value == '-' or value == '':
        return None
    
    # Handle suffixes
    multiplier = 1
    if value.endswith('K'):
        multiplier = 1000
        value = value[:-1]
    elif value.endswith('M'):
        multiplier = 1000000
        value = value[:-1]
    elif value.endswith('B'):
        multiplier = 1000000000
        value = value[:-1]
    
    try:
        # Remove commas and convert
        value = value.replace(',', '')
        return float(value) * multiplier
    except (ValueError, AttributeError):
        return None

def parse_percentage(value: str) -> Optional[float]:
    """Parse a percentage string"""
    if not value or value == '-' or value.strip() == '':
        return None
    
    value = value.replace('%', '').strip()
    if value == '-' or value == '':
        return None
    
    try:
        return float(value)
    except (ValueError, AttributeError):
        return None

def scrape_page(url: str, page_num: int = 1) -> List[Dict]:
    """Helper function to scrape a single page"""
    # Add page parameter if not page 1
    # Try different pagination formats
    if page_num > 1:
        if '?' in url:
            # Try ?page= first
            page_url = f"{url}&page={page_num}"
        else:
            page_url = f"{url}?page={page_num}"
    else:
        page_url = url
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    response = requests.get(page_url, headers=headers, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find all tables - usually the data table is the second one
    all_tables = soup.find_all('table')
    table = None
    
    # Find the table with the most rows (likely the data table)
    max_rows = 0
    for t in all_tables:
        row_count = len(t.find_all('tr'))
        if row_count > max_rows:
            max_rows = row_count
            table = t
    
    if not table or max_rows < 2:
        return []  # Return empty list if no table found
    
    # Extract table rows - skip header row
    all_rows = table.find_all('tr')
    if len(all_rows) < 2:
        return []
    
    # First row is usually the header
    data_rows = all_rows[1:]  # Skip first row (header)
    
    rows = []
    for tr in data_rows:
        cells = tr.find_all(['td', 'th'])
        
        # Need at least 5 cells for valid data row
        if len(cells) < 5:
            continue
        
        row_data = {}
        cell_index = 0
        
        for cell in cells:
            cell_text = cell.get_text(strip=True)
            
            # Skip empty cells and "Buy Now" buttons
            if not cell_text or cell_text.lower() in ['buy now', '']:
                continue
            
            # Map cells to data fields based on position
            if cell_index == 0:
                # Symbol - might be in a link
                link = cell.find('a')
                symbol = link.get_text(strip=True) if link else cell_text
                if symbol and len(symbol) <= 10:  # Symbols are usually short
                    row_data['symbol'] = symbol
                    cell_index += 1
            elif cell_index == 1:
                # Current Short Int.
                row_data['current_short_int'] = parse_percentage(cell_text)
                cell_index += 1
            elif cell_index == 2:
                # Previous Short Int.
                row_data['previous_short_int'] = parse_percentage(cell_text)
                cell_index += 1
            elif cell_index == 3:
                # Short Int. Change (might be empty)
                if cell_text and cell_text != '-':
                    row_data['short_int_change'] = parse_number(cell_text)
                cell_index += 1
            elif cell_index == 4:
                # Short Int. % Change
                row_data['short_int_pct_change'] = parse_percentage(cell_text)
                cell_index += 1
            elif cell_index == 5:
                # Days to Cover
                row_data['days_to_cover'] = parse_number(cell_text)
                cell_index += 1
            elif cell_index == 6:
                # Shares Short Value
                row_data['shares_short_value'] = cell_text
                cell_index += 1
            elif cell_index == 7:
                # Avg Daily Volume
                row_data['avg_daily_volume'] = cell_text
                cell_index += 1
            elif cell_index == 8:
                # Market Cap
                row_data['market_cap'] = cell_text
                cell_index += 1
            elif cell_index > 8:
                # Stop processing if we've gone past expected columns
                break
        
        # Only add row if it has a symbol and at least one other data field
        if row_data.get('symbol') and len([k for k in row_data.keys() if k != 'symbol']) > 0:
            rows.append(row_data)
    
    return rows

def get_total_pages(url: str) -> int:
    """Try to determine total number of pages from pagination"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for pagination elements
        pagination_text = soup.get_text()
        
        # Try to find page numbers in pagination
        # Look for patterns like "1 2 3 4 5 ... 11" or "Page X of Y"
        page_numbers = re.findall(r'\b(\d+)\b', pagination_text)
        
        # If we find numbers, try to get the largest reasonable one (likely total pages)
        # Filter out obviously wrong numbers (too large, too small)
        potential_pages = [int(n) for n in page_numbers if 1 <= int(n) <= 100]
        if potential_pages:
            max_page = max(potential_pages)
            # If max page is reasonable, use it; otherwise default to 11 (common for 100/page)
            if max_page <= 50:
                return max_page
        
        # Default: try up to 20 pages, stop when we get empty results
        return 20
    except:
        return 20  # Default fallback

@router.get("/most-shorted")
async def get_most_shorted_stocks(page: Optional[int] = None):
    """
    Scrape Benzinga's most shorted stocks page and return the data table.
    If page is not specified, scrapes all pages.
    """
    try:
        base_url = "https://www.benzinga.com/short-interest/most-shorted"
        
        all_rows = []
        
        if page:
            # Scrape specific page
            rows = scrape_page(base_url, page)
            all_rows.extend(rows)
        else:
            # Scrape all pages - continue until we get duplicate or empty results
            seen_symbols = set()
            page_num = 1
            max_pages = 20  # Safety limit
            
            while page_num <= max_pages:
                try:
                    rows = scrape_page(base_url, page_num)
                    if not rows:
                        # If we get empty results, we've reached the end
                        break
                    
                    # Check if we're getting duplicate data (same symbols as previous page)
                    current_symbols = {row.get('symbol') for row in rows if row.get('symbol')}
                    if current_symbols and current_symbols.issubset(seen_symbols):
                        # All symbols are duplicates, we've reached the end
                        break
                    
                    # Add new rows and track symbols
                    all_rows.extend(rows)
                    seen_symbols.update(current_symbols)
                    
                    # Small delay to be respectful
                    time.sleep(0.5)
                    page_num += 1
                except Exception as e:
                    print(f"Error scraping page {page_num}: {e}")
                    # If we've gotten some data, break on error; otherwise continue
                    if all_rows:
                        break
                    page_num += 1
                    continue
        
        return {
            "data": all_rows,
            "total_rows": len(all_rows),
            "pages_scraped": page if page else "all",
            "updated_at": datetime.utcnow().isoformat(),
            "source": "Benzinga"
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch data from Benzinga: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error parsing short interest data: {str(e)}"
        )

@router.get("/largest-increase")
async def get_largest_increase(page: Optional[int] = None):
    """
    Scrape Benzinga's largest increase in short interest page.
    If page is not specified, scrapes all pages.
    """
    try:
        base_url = "https://www.benzinga.com/short-interest/largest-increase"
        
        all_rows = []
        
        if page:
            rows = scrape_page(base_url, page)
            all_rows.extend(rows)
        else:
            # Scrape all pages - continue until we get duplicate or empty results
            seen_symbols = set()
            page_num = 1
            max_pages = 20
            
            while page_num <= max_pages:
                try:
                    rows = scrape_page(base_url, page_num)
                    if not rows:
                        break
                    
                    current_symbols = {row.get('symbol') for row in rows if row.get('symbol')}
                    if current_symbols and current_symbols.issubset(seen_symbols):
                        break
                    
                    all_rows.extend(rows)
                    seen_symbols.update(current_symbols)
                    time.sleep(0.5)
                    page_num += 1
                except Exception as e:
                    print(f"Error scraping page {page_num}: {e}")
                    if all_rows:
                        break
                    page_num += 1
                    continue
        
        return {
            "data": all_rows,
            "total_rows": len(all_rows),
            "pages_scraped": page if page else "all",
            "updated_at": datetime.utcnow().isoformat(),
            "source": "Benzinga"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching largest increase data: {str(e)}"
        )

@router.get("/largest-decrease")
async def get_largest_decrease(page: Optional[int] = None):
    """
    Scrape Benzinga's largest decrease in short interest page.
    If page is not specified, scrapes all pages.
    """
    try:
        base_url = "https://www.benzinga.com/short-interest/largest-decrease"
        
        all_rows = []
        
        if page:
            rows = scrape_page(base_url, page)
            all_rows.extend(rows)
        else:
            # Scrape all pages - continue until we get duplicate or empty results
            seen_symbols = set()
            page_num = 1
            max_pages = 20
            
            while page_num <= max_pages:
                try:
                    rows = scrape_page(base_url, page_num)
                    if not rows:
                        break
                    
                    current_symbols = {row.get('symbol') for row in rows if row.get('symbol')}
                    if current_symbols and current_symbols.issubset(seen_symbols):
                        break
                    
                    all_rows.extend(rows)
                    seen_symbols.update(current_symbols)
                    time.sleep(0.5)
                    page_num += 1
                except Exception as e:
                    print(f"Error scraping page {page_num}: {e}")
                    if all_rows:
                        break
                    page_num += 1
                    continue
        
        return {
            "data": all_rows,
            "total_rows": len(all_rows),
            "pages_scraped": page if page else "all",
            "updated_at": datetime.utcnow().isoformat(),
            "source": "Benzinga"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching largest decrease data: {str(e)}"
        )

