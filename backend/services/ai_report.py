import json
import logging
import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
import models
from services.agent import agent_service
from services.market import indices, crypto, currency, commodity, economic
# Import routers for functions not in services (Bond, Calendar)
# Note: Importing routers in services can be risky for circular deps, 
# but assuming routers don't import this service yet.
from routers.market.bond import routes as bond_routes
from routers.framework import routes as framework_routes

logger = logging.getLogger(__name__)

async def collect_market_data():
    """
    Aggregate data from all market categories.
    Returns a dictionary with organized market data.
    """
    data = {
        "generated_at": datetime.datetime.now().isoformat(),
        "equity": {},
        "bond": {},
        "currency": {},
        "commodity": {},
        "crypto": {},
        "economic": {},
        "calendar": {}
    }

    try:
        # 1. Equity: Indices
        # We need generic indices data (Major US + Global)
        # using 'daily' timeframe for report
        major_indices = await indices.fetch_major_indices_data()
        regional_indices = await indices.fetch_regional_indices_data()
        data["equity"]["major_indices"] = major_indices
        data["equity"]["regional_indices"] = regional_indices
    except Exception as e:
        logger.error(f"Error collecting equity data: {e}")
        data["equity"]["error"] = str(e)

    try:
        # 2. Bond
        # Using the router's get_all_bond_data function
        bond_data = await bond_routes.get_all_bond_data(timeframe="monthly") # Monthly gives context, or daily? 
        # For report, maybe we want recent moves. The router defaults to monthly (1y) history.
        # We just need current values mostly.
        data["bond"] = bond_data
    except Exception as e:
        logger.error(f"Error collecting bond data: {e}")
        data["bond"]["error"] = str(e)

    try:
        # 3. Currency
        curr_data = await currency.fetch_currency_data(timeframe="monthly")
        data["currency"] = curr_data
    except Exception as e:
        logger.error(f"Error collecting currency data: {e}")
        data["currency"]["error"] = str(e)

    try:
        # 4. Commodity
        comm_data = await commodity.fetch_commodity_data(timeframe="monthly")
        data["commodity"] = comm_data
    except Exception as e:
        logger.error(f"Error collecting commodity data: {e}")
        data["commodity"]["error"] = str(e)

    try:
        # 5. Crypto
        # Fetch top coins
        crypto_data = await crypto.fetch_crypto_data(timeframe="daily")
        data["crypto"] = crypto_data
    except Exception as e:
        logger.error(f"Error collecting crypto data: {e}")
        data["crypto"]["error"] = str(e)

    try:
        # 6. Economic
        eco_data = await economic.fetch_all_economic_data(timeframe="monthly")
        data["economic"]["indicators"] = eco_data
    except Exception as e:
        logger.error(f"Error collecting economic data: {e}")
        data["economic"]["error"] = str(e)

    try:
        # 7. Calendar
        # Import get_economic_calendar from framework routes
        cal_data = await framework_routes.get_economic_calendar()
        data["calendar"] = cal_data
    except Exception as e:
        logger.error(f"Error collecting calendar data: {e}")
        data["calendar"]["error"] = str(e)

    return data

def format_data_for_agent(data: dict) -> str:
    """
    Format the raw data dictionary into a readable string for the AI agent.
    Truncates generic history lists to save tokens, keeping latest values.
    """
    # Create a simplified version of data for the prompt
    
    summary = []
    summary.append(f"MARKET REPORT DATA ({data.get('generated_at')})")
    summary.append("=" * 50)

    # Helper to format list of assets
    def format_list(title, items, key_name='name', val_name='value', change_name='changesPercentage'):
        lines = [f"\n## {title}"]
        if not items:
            lines.append("No data available.")
            return "\n".join(lines)
        
        # Limit to top 20 items to avoid token overflow
        for item in items[:20]:
            name = item.get(key_name) or item.get('symbol') or item.get('title')
            val = item.get(val_name) or item.get('price') or item.get('current_value')
            change = item.get(change_name) or item.get('change_percent') or 0
            
            line = f"- {name}: {val}"
            if change:
                line += f" ({change}%)"
            lines.append(line)
        return "\n".join(lines)

    # Equity
    if "equity" in data:
        major = data["equity"].get("major_indices", [])
        summary.append(format_list("Equity: Major Indices", major, 'symbol', 'price', 'changesPercentage'))

    # Bond
    if "bond" in data:
        # Bond data is structured by categories in the router return
        bonds = data["bond"]
        summary.append("\n## Bond Market")
        for cat, items in bonds.items():
            summary.append(f"\n### {cat}")
            for item in items:
                title = item.get('title')
                val = item.get('current_value')
                summary.append(f"- {title}: {val}")

    # Currency
    if "currency" in data:
        curr = data["currency"]
        summary.append(format_list("Currency", curr, 'ticker', 'price', 'changesPercentage'))

    # Commodity
    if "commodity" in data:
        comm = data["commodity"]
        summary.append(format_list("Commodities", comm, 'name', 'price', 'changesPercentage'))

    # Crypto
    if "crypto" in data:
        cry = data["crypto"]
        summary.append(format_list("Crypto", cry, 'symbol', 'price', 'changesPercentage'))

    # Economic
    if "economic" in data:
        eco = data["economic"].get("indicators", [])
        summary.append(format_list("Economic Indicators (Latest)", eco, 'indicator', 'value', ''))

    # Calendar
    if "calendar" in data:
        cal = data["calendar"]
        summary.append("\n## Economic Calendar (Upcoming)")
        if isinstance(cal, list):
            for event in cal[:20]: # Limit
                date = event.get('date') or event.get('formatted_date')
                event_name = event.get('event')
                country = event.get('country')
                impact = event.get('impact')
                summary.append(f"- {date} [{country}] {event_name} (Impact: {impact})")
        else:
             summary.append("No calendar data.")

    return "\n".join(summary)

async def generate_market_report(manual_trigger=False):
    """
    Main function to generate the daily market report.
    """
    logger.info("Starting Market Report Generation...")
    
    # 1. Collect Data
    data = await collect_market_data()
    
    # 2. Format for AI
    context = format_data_for_agent(data)
    
    # 3. Generate Report Content
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    prompt_customization = """
    Create a professional "Daily Market Report" based on the provided data.
    
    Structure the report with the following sections:
    1. **Market Overview**: Key takeaways and sentiment sumary.
    2. **Equity**: Analysis of major indices and market movers.
    3. **Bond Market**: Treasury yields, curve analysis, and stress metrics.
    4. **Currency**: Key FX pairs and dollar strength/weakness.
    5. **Commodities**: Energy, Metals, and Agriculture trends.
    6. **Crypto**: Major crypto assets performance.
    7. **Economic Calendar**: Upcoming key events and their potential impact.

    Format in Markdown. Use tables where appropriate for data comparison. 
    Be concise but insightful. Highlight anomalies or significant moves.
    """
    
    try:
        report_content = await agent_service.generate_report(context, prompt_customization)
    except Exception as e:
        logger.error(f"AI Generation failed: {e}")
        return False

    # 4. Save to Database
    db = SessionLocal()
    try:
        # Create a "Market" type report
        # User ID? We need an admin user ID or a system user. 
        # Let's assign to the first admin found, or a specific "System" user if exists.
        # For now, search for 'admin' role.
        admin_user = db.query(models.User).filter(models.User.role == "admin").first()
        user_id = admin_user.id if admin_user else 1 # Fallback
        
        # We save the HTML/Markdown content directly? 
        # ReportView expects PDF path in 'content' for 'is_uploaded=True', or HTML for 'is_uploaded=False'?
        # The prompt says "Market Reports ... in ReportView ... to support Markdown/HTML".
        # So we create `is_uploaded=False` report.
        
        db_report = models.Report(
            title=f"Market Report - {today_str}",
            content=report_content,
            report_type="market",
            ticker="MARKET", # generic ticker
            user_id=user_id,
            is_uploaded=False,
            created_at=datetime.datetime.utcnow()
        )
        db.add(db_report)
        db.commit()
        logger.info(f"Market Report saved (ID: {db_report.id})")
        return True
    except Exception as e:
        logger.error(f"Database save failed: {e}")
        db.rollback()
        return False
    finally:
        db.close()
