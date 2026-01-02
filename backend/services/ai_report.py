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
import markdown
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
import boto3
import uuid
import os

# S3/MinIO Configuration
# Prefer AWS_ variables (Railway/Production), fallback to S3_/MINIO_ (Local)
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME") or os.getenv("S3_BUCKET_NAME", "reports")
S3_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL") or os.getenv("S3_ENDPOINT_URL", "http://localhost:9000")

# Ensure endpoint has protocol
if S3_ENDPOINT_URL and not (S3_ENDPOINT_URL.startswith('http://') or S3_ENDPOINT_URL.startswith('https://')):
    S3_ENDPOINT_URL = f"https://{S3_ENDPOINT_URL}" # Default to https for remote, http usually explicit for local

logger = logging.getLogger(__name__)

# Log S3 Configuration (Masking credentials)
logger.info("-" * 40)
logger.info(f"S3 Configuration:")
logger.info(f"  Endpoint: {S3_ENDPOINT_URL}")
logger.info(f"  Bucket:   {S3_BUCKET_NAME}")
logger.info(f"  Region:   {AWS_DEFAULT_REGION}")
logger.info("-" * 40)

s3_client = boto3.client(
    's3',
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    config=boto3.session.Config(signature_version='s3v4'),
    region_name=AWS_DEFAULT_REGION
)

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
        sectors = await indices.fetch_sector_performance()
        industries = await indices.fetch_industry_performance()
        data["equity"]["major_indices"] = major_indices
        data["equity"]["regional_indices"] = regional_indices
        data["equity"]["sectors"] = sectors
        data["equity"]["industries"] = industries
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
            name = item.get(key_name) or item.get('symbol') or item.get('title') or "Unknown"
            val = item.get(val_name) or item.get('price') or item.get('current_value') or item.get('close')
            change = item.get(change_name) or item.get('change_percent') or item.get('change') or 0
            
            line = f"- {name}: {val}"
            if change:
                line += f" ({change}%)"
            lines.append(line)
        return "\n".join(lines)

    # Equity
    if "equity" in data:
        if "error" in data["equity"]:
             summary.append(f"\n## Equity\nError collecting data: {data['equity']['error']}")
        else:
            major = data["equity"].get("major_indices", [])
            # major_indices returns {name, key, value, change}
            summary.append(format_list("Equity: Major Indices", major, 'name', 'value', 'change'))
            
            regional = data["equity"].get("regional_indices", {})
            if regional:
                summary.append("\n## Equity: Regional Indices")
                for region, indices in regional.items():
                    summary.append(f"\n### {region}")
                    for idx in indices:
                        # regional returns {symbol, name, price, changePercent...}
                        summary.append(f"- {idx.get('name')}: {idx.get('price')} ({idx.get('changePercent')}%)")

            sectors = data["equity"].get("sectors", [])
            if sectors:
                 # sector data: {sector: Name, changesPercentage: Val}
                 summary.append(format_list("Equity: Sector Performance", sectors, 'sector', 'changesPercentage', ''))

            industries = data["equity"].get("industries", [])
            if industries:
                 summary.append(format_list("Equity: Top/Bottom Industries", industries, 'industry', 'changesPercentage', ''))


    # Bond
    if "bond" in data:
        bonds = data["bond"]
        if "error" in bonds:
            summary.append(f"\n## Bond Market\nError collecting data: {bonds['error']}")
        else:
            summary.append("\n## Bond Market")
            for cat, items in bonds.items():
                if not isinstance(items, list): continue
                summary.append(f"\n### {cat}")
                for item in items:
                    if not isinstance(item, dict): continue
                    title = item.get('title')
                    val = item.get('current_value')
                    summary.append(f"- {title}: {val}")

    # Currency
    if "currency" in data:
        curr = data["currency"]
        if isinstance(curr, dict) and "error" in curr:
             summary.append(f"\n## Currency\nError collecting data: {curr['error']}")
        elif isinstance(curr, dict):
             # curr is { symbol: [ {date, value}... ] }
             curr_clean = []
             for sym, hist in curr.items():
                 if not hist: continue
                 # hist is sorted by date
                 latest = hist[-1]
                 val = latest['value']
                 change = 0
                 if len(hist) > 1:
                     prev = hist[-2]['value']
                     if prev != 0:
                        change = ((val - prev) / prev) * 100
                 curr_clean.append({'ticker': sym, 'price': round(val, 4), 'change': round(change, 2)})
             
             summary.append(format_list("Currency", curr_clean, 'ticker', 'price', 'change'))
        elif isinstance(curr, list):
             summary.append(format_list("Currency", curr, 'ticker', 'price', 'changesPercentage'))

    # Commodity
    if "commodity" in data:
        comm = data["commodity"]
        if isinstance(comm, dict) and "error" in comm:
             summary.append(f"\n## Commodities\nError collecting data: {comm['error']}")
        elif isinstance(comm, dict):
             # comm is { Category: [ {symbol, name, price, changePercent...} ] }
             summary.append("\n## Commodities")
             for cat, items in comm.items():
                  if not items: continue
                  summary.append(f"\n### {cat}")
                  for item in items:
                      n = item.get('name')
                      p = item.get('price')
                      c = item.get('changePercent')
                      summary.append(f"- {n}: {p} ({c}%)")
        elif isinstance(comm, list):
             summary.append(format_list("Commodities", comm, 'name', 'price', 'changesPercentage'))

    # Crypto
    if "crypto" in data:
        cry = data["crypto"]
        if isinstance(cry, dict) and "error" in cry:
             summary.append(f"\n## Crypto\nError collecting data: {cry['error']}")
        elif isinstance(cry, list):
             # crypto returns {symbol, price, changesPercentage}
             summary.append(format_list("Crypto", cry, 'name', 'price', 'changesPercentage'))

    # Economic
    if "economic" in data:
        if "error" in data["economic"]:
             summary.append(f"\n## Economic Indicators\nError collecting data: {data['economic']['error']}")
        else:
             eco = data["economic"].get("indicators", [])
             summary.append(format_list("Economic Indicators (Latest)", eco, 'indicator', 'value', ''))

    # Calendar
    if "calendar" in data:
        cal = data["calendar"]
        summary.append("\n## Economic Calendar (Upcoming)")
        if isinstance(cal, list):
            for event in cal[:20]:
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
    prompt_customization = f"""
    Create a professional "Daily Market Report - {today_str}" based on the provided data.
    
    Structure the report with the following sections:
    1. **Market Overview**: Comprehensive analysis, predictions, and risk assessment. Synthesize the data to provide a conclusion on market direction. Support with key data points. Use bullet points.
    2. **Equity**: Analysis of major indices, regional markets, SECTOR, and INDUSTRY performance. Identify leading/lagging sectors and notable industry moves.
    3. **Bond Market**: Treasury yields, curve analysis, and stress metrics.
    4. **Currency**: Key FX pairs and dollar strength/weakness. Cite specific rates.
    5. **Commodities**: Energy, Metals, and Agriculture trends. Cite specific prices.
    6. **Crypto**: Major crypto assets performance (e.g. Bitcoin, Ethereum). Identify assets by NAME. Use bullet points with data driven insights.
    7. **Economic Calendar**: Key Medium/High impact events. MUST list specific Date & Time for each event.

    Format in Markdown. 
    **TONE**: Straightforward, critical, and human-like (avoid robotic hedging).
    
    **CRITICAL**: 
    - Use bullet points for lists and readability.
    - Support all claims with DATA (prices, % changes) from the input.
    - Do not state "absence of data" unless truly empty.
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
        
        # Convert Markdown to PDF
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Simple Markdown parsing (ReportLab doesn't support full MD natively, so we do basic cleanup)
        # For a production app, we might want markdown2pdf or similar, but let's do a simple pass
        # Convert MD to HTML-ish compatible with ReportLab or just plain paragraphs
        
        # Title
        story.append(Paragraph(f"Daily Market Report - {today_str}", styles['Title']))
        story.append(Spacer(1, 12))
        
        # Process lines
        lines = report_content.split('\n')
        for line in lines:
            if line.startswith('## '):
                story.append(Paragraph(line.replace('## ', ''), styles['Heading2']))
            elif line.startswith('### '):
                story.append(Paragraph(line.replace('### ', ''), styles['Heading3']))
            elif line.startswith('- ') or line.startswith('* '):
                 story.append(Paragraph(line.replace('- ', '• ').replace('* ', '• '), styles['BodyText']))
            elif line.strip():
                story.append(Paragraph(line, styles['BodyText']))
            story.append(Spacer(1, 6))

        doc.build(story)
        pdf_value = pdf_buffer.getvalue()
        
        # Upload to S3
        report_uuid = str(uuid.uuid4())
        file_path = f"Market/{today_str}/{report_uuid}.pdf"
        
        try:
            s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=file_path,
                Body=pdf_value,
                ContentType='application/pdf'
            )
            is_uploaded = True
            logging.info(f"Uploaded PDF to S3: {file_path}")
            # Save MinIO path in content field as per user request to restructure storage
            # content will be: minio://bucket/path
            final_content = f"minio://{S3_BUCKET_NAME}/{file_path}"
        except Exception as s3_err:
            logging.error(f"Failed to upload PDF to S3: {s3_err}")
            is_uploaded = False
            file_path = None 
            final_content = report_content # Fallback to saving text content

        db_report = models.Report(
            title=f"Market Report - {today_str}",
            content=final_content,
            report_type="market",
            ticker="MARKET",
            user_id=user_id,
            is_uploaded=is_uploaded, 
            file_path=file_path,
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
