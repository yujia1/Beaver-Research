"""
Service to fetch, parse, and process 13F filings from SEC EDGAR.
Handles batch processing, CSV generation, MinIO storage, and quarter-over-quarter comparisons.
"""
import requests
import os
import json
import csv
import io
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from xml.etree import ElementTree as ET
import boto3
from botocore.client import Config
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import pandas as pd

from database import get_db
from models import Filing13F
from services.edgar_service import EdgarService


class Filing13FService:
    """Service for processing 13F institutional holdings filings"""
    
    def __init__(self):
        self.edgar_service = EdgarService()
        self.headers = {
            "User-Agent": "FinancialDashboard contact@example.com"
        }
        
        # MinIO configuration
        self.minio_endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        self.minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        self.minio_bucket = os.getenv("MINIO_BUCKET", "reports")
        self.minio_use_ssl = os.getenv("MINIO_USE_SSL", "false").lower() == "true"
        
        # CUSIP to ticker cache
        self.cusip_cache = {}
        
        # 13F deadlines: 45 days after quarter-end
        # Q1 (Jan-Mar) -> May 15
        # Q2 (Apr-Jun) -> Aug 14
        # Q3 (Jul-Sep) -> Nov 14
        # Q4 (Oct-Dec) -> Feb 14
        self.quarter_deadlines = {
            "Q1": (5, 15),  # May 15
            "Q2": (8, 14),  # Aug 14
            "Q3": (11, 14), # Nov 14
            "Q4": (2, 14),  # Feb 14 (next year)
        }
        
    def _get_minio_client(self):
        """Get MinIO client"""
        # Determine protocol
        protocol = 'https' if self.minio_use_ssl else 'http'
        
        # Check if endpoint already has protocol
        if self.minio_endpoint.startswith('http://') or self.minio_endpoint.startswith('https://'):
            endpoint_url = self.minio_endpoint
        else:
            endpoint_url = f"{protocol}://{self.minio_endpoint}"
        
        return boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=self.minio_access_key,
            aws_secret_access_key=self.minio_secret_key,
            config=Config(signature_version='s3v4'),
            region_name='us-east-1'
        )
    
    def _ensure_bucket_exists(self):
        """Ensure MinIO bucket exists"""
        try:
            client = self._get_minio_client()
            client.head_bucket(Bucket=self.minio_bucket)
        except:
            try:
                client = self._get_minio_client()
                client.create_bucket(Bucket=self.minio_bucket)
            except Exception as e:
                print(f"Warning: Could not create bucket {self.minio_bucket}: {e}")
    
    def get_quarter_from_date(self, date: datetime) -> str:
        """Get quarter string (YYYY-Q1, YYYY-Q2, etc.) from date"""
        year = date.year
        month = date.month
        if month <= 3:
            quarter = "Q1"
        elif month <= 6:
            quarter = "Q2"
        elif month <= 9:
            quarter = "Q3"
        else:
            quarter = "Q4"
        return f"{year}-{quarter}"
    
    def get_quarter_deadline(self, quarter: str) -> datetime:
        """Get the filing deadline for a quarter"""
        year, q = quarter.split("-")
        year = int(year)
        month, day = self.quarter_deadlines[q]
        
        # Q4 deadline is in the next year
        if q == "Q4":
            year += 1
            
        return datetime(year, month, day)
    
    def should_process_quarter(self, quarter: str) -> bool:
        """Check if we should process filings for this quarter (2-3 days after deadline)"""
        deadline = self.get_quarter_deadline(quarter)
        # Process 2-3 days after deadline
        process_start = deadline + timedelta(days=2)
        process_end = deadline + timedelta(days=3)
        now = datetime.now()
        
        return process_start <= now <= process_end
    
    def get_all_13f_filings(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get all 13F filings from EDGAR master index files.
        This is more efficient than querying per-CIK.
        """
        filings = []
        
        # EDGAR master index files are organized by year/quarter
        # Format: https://www.sec.gov/Archives/edgar/full-index/YYYY/QTRX/master.idx
        
        if not start_date:
            # Default to last 2 quarters
            start_date = datetime.now() - timedelta(days=180)
        if not end_date:
            end_date = datetime.now()
        
        current_date = start_date
        while current_date <= end_date:
            year = current_date.year
            quarter = (current_date.month - 1) // 3 + 1
            
            try:
                url = f"https://www.sec.gov/Archives/edgar/full-index/{year}/QTR{quarter}/master.idx"
                response = requests.get(url, headers=self.headers, timeout=30)
                
                if response.status_code == 200:
                    lines = response.text.split('\n')
                    # Skip header lines (first 10 lines typically)
                    for line in lines[10:]:
                        if not line.strip():
                            continue
                        
                        # Master index format: CIK|Company Name|Form Type|Date Filed|Filename
                        parts = line.split('|')
                        if len(parts) >= 5:
                            form_type = parts[2].strip()
                            if form_type in ['13F-HR', '13F-HR/A', '13F-NT']:
                                filing_date_str = parts[3].strip()
                                try:
                                    filing_date = datetime.strptime(filing_date_str, '%Y-%m-%d')
                                    if start_date <= filing_date <= end_date:
                                        filings.append({
                                            'cik': parts[0].strip(),
                                            'company_name': parts[1].strip(),
                                            'form_type': form_type,
                                            'filing_date': filing_date,
                                            'filename': parts[4].strip(),
                                            'accession_number': parts[4].strip().split('/')[-1].replace('.txt', '')
                                        })
                                except ValueError:
                                    continue
            except Exception as e:
                print(f"Error fetching master index for {year} Q{quarter}: {e}")
            
            # Move to next quarter
            if quarter == 4:
                current_date = datetime(year + 1, 1, 1)
            else:
                current_date = datetime(year, quarter * 3 + 1, 1)
        
        return filings
    
    def get_filing_content(self, cik: str, accession_number: str) -> Optional[str]:
        """Get the content of a 13F filing"""
        try:
            # Remove dashes from accession number
            accession_clean = accession_number.replace('-', '')
            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{accession_number}.txt"
            
            response = requests.get(url, headers=self.headers, timeout=30)
            if response.status_code == 200:
                content = response.text
                
                # Check if there's a separate XML file with holdings (informationTable)
                # Look for XML file references in the content
                import re
                xml_files = re.findall(r'<FILENAME>([^<]+\.xml)', content, re.IGNORECASE)
                
                # Try to find the informationTable XML file (usually has a pattern like *13f.xml or informationTable.xml)
                info_table_file = None
                for xml_file in xml_files:
                    if '13f' in xml_file.lower() or 'information' in xml_file.lower():
                        info_table_file = xml_file
                        break
                
                # If no specific file found, try the first XML file that's not primary_doc.xml
                if not info_table_file and xml_files:
                    for xml_file in xml_files:
                        if 'primary' not in xml_file.lower():
                            info_table_file = xml_file
                            break
                
                # Fetch the informationTable XML file if found
                if info_table_file:
                    xml_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_clean}/{info_table_file}"
                    xml_response = requests.get(xml_url, headers=self.headers, timeout=30)
                    if xml_response.status_code == 200:
                        # Return both: main content for metadata, XML file for holdings
                        return {
                            'main': content,
                            'xml': xml_response.text,
                            'xml_file': info_table_file
                        }
                
                return content
        except Exception as e:
            print(f"Error fetching filing {accession_number} for CIK {cik}: {e}")
        
        return None
    
    def parse_13f_xml(self, content: str, xml_file_content: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Parse 13F XML content and extract holdings"""
        try:
            # 13F filings can have XML in different formats:
            # 1. Embedded in <XML> tags
            # 2. As separate XML document
            # 3. Embedded in HTML with <edgarSubmission>
            
            xml_content = None
            
            # Strategy 1: Look for <XML> tags
            xml_start = content.find('<XML>')
            if xml_start != -1:
                xml_end = content.find('</XML>', xml_start)
                if xml_end != -1:
                    # Extract content inside <XML> tags (skip the tags themselves)
                    xml_content = content[xml_start + 5:xml_end].strip()  # +5 to skip <XML>
                    # Remove XML declaration if present (it's not needed and causes issues)
                    if xml_content.startswith('<?xml'):
                        decl_end = xml_content.find('?>')
                        if decl_end != -1:
                            xml_content = xml_content[decl_end + 2:].strip()
            
            # Strategy 2: Look for <edgarSubmission> (most common)
            if xml_content is None:
                edgar_start = content.find('<edgarSubmission')
                if edgar_start != -1:
                    # Find the matching closing tag
                    edgar_end = content.rfind('</edgarSubmission>')
                    if edgar_end != -1:
                        xml_content = content[edgar_start:edgar_end + len('</edgarSubmission>')]
            
            # Strategy 3: Look for infoTable directly (fallback)
            if xml_content is None:
                info_start = content.find('<infoTable>')
                if info_start != -1:
                    # Find all infoTable sections and wrap them
                    import re
                    info_tables = re.findall(r'<infoTable>.*?</infoTable>', content, re.DOTALL)
                    if info_tables:
                        xml_content = f'<root>{"".join(info_tables)}</root>'
            
            if xml_content is None:
                return None
            
            # Clean up XML content
            xml_content = xml_content.strip()
            
            # Remove BOM if present
            if xml_content.startswith('\ufeff'):
                xml_content = xml_content[1:]
            
            # Remove any leading text before first <
            first_tag = xml_content.find('<')
            if first_tag > 0:
                xml_content = xml_content[first_tag:]
            
            # Remove XML declaration if it's not at the start (causes parse errors)
            if '<?xml' in xml_content and not xml_content.strip().startswith('<?xml'):
                # Find and remove XML declaration
                decl_end = xml_content.find('?>')
                if decl_end != -1:
                    xml_content = xml_content[decl_end + 2:].lstrip()
            
            # Parse XML
            try:
                root = ET.fromstring(xml_content)
            except ET.ParseError:
                # Try to extract just infoTable sections as last resort
                import re
                info_tables = re.findall(r'<infoTable>.*?</infoTable>', xml_content, re.DOTALL)
                if info_tables:
                    xml_content = f'<root>{"".join(info_tables)}</root>'
                    root = ET.fromstring(xml_content)
                else:
                    raise
            
            # Remove namespace prefixes for easier parsing
            def remove_namespace(elem):
                if elem.tag.startswith('{'):
                    elem.tag = elem.tag.split('}')[1]
                for child in elem:
                    remove_namespace(child)
            
            remove_namespace(root)
            
            # Extract header information
            header_info = {}
            header = root.find('.//headerData')
            if header is not None:
                for child in header:
                    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    header_info[tag] = child.text
            
            # Extract period end date
            period_end = None
            period_end_elem = root.find('.//periodOfReport')
            if period_end_elem is None:
                period_end_elem = root.find('.//periodOfReportDate')
            if period_end_elem is not None:
                period_end_str = period_end_elem.text
                if period_end_str:
                    # Try various date formats
                    date_formats = ['%m-%d-%Y', '%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d', '%Y%m%d']
                    for fmt in date_formats:
                        try:
                            period_end = datetime.strptime(period_end_str.strip(), fmt)
                            break
                        except:
                            continue
            
            # Extract holdings
            holdings = []
            info_tables = root.findall('.//infoTable')
            
            # If no infoTable found and we have a separate XML file, try parsing that
            if not info_tables and xml_file_content:
                return self._parse_information_table_xml(xml_file_content, period_end, header_info)
            
            for info_table in info_tables:
                holding = {}
                for child in info_table:
                    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    text = child.text
                    
                    if tag == 'shrsOrPrnAmt':
                        # Handle nested structure for shares
                        ssh_prnamt = child.find('sshPrnamt')
                        if ssh_prnamt is None:
                            ssh_prnamt = child.find('.//sshPrnamt')
                        if ssh_prnamt is not None and ssh_prnamt.text:
                            try:
                                shares_text = ssh_prnamt.text.replace(',', '').strip()
                                holding['shares'] = int(float(shares_text))
                            except:
                                holding['shares'] = ssh_prnamt.text
                        ssh_prnamt_type = child.find('sshPrnamtType')
                        if ssh_prnamt_type is None:
                            ssh_prnamt_type = child.find('.//sshPrnamtType')
                        if ssh_prnamt_type is not None:
                            holding['sharesType'] = ssh_prnamt_type.text
                    elif tag == 'value':
                        # Remove commas and convert to int (cents for value)
                        if text:
                            text = text.replace(',', '').replace('$', '').strip()
                            try:
                                holding[tag] = int(float(text) * 100)  # Convert to cents
                            except:
                                holding[tag] = text
                    elif tag in ['sshPrnamt', 'sshPrnamtType']:
                        # Skip these as they're handled in shrsOrPrnAmt
                        continue
                    else:
                        holding[tag] = text
                
                holdings.append(holding)
            
            return {
                'header': header_info,
                'period_end': period_end,
                'holdings': holdings
            }
            
        except Exception as e:
            print(f"Error parsing 13F XML: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_information_table_xml(self, xml_content: str, period_end: Optional[datetime], header_info: Dict) -> Optional[Dict[str, Any]]:
        """Parse the separate informationTable XML file"""
        try:
            # This XML uses a different namespace
            root = ET.fromstring(xml_content)
            
            # Namespace for informationTable
            ns = {'info': 'http://www.sec.gov/edgar/document/thirteenf/informationtable'}
            
            # Find all infoTable elements
            info_tables = root.findall('.//info:infoTable', ns)
            
            holdings = []
            for info_table in info_tables:
                holding = {}
                for child in info_table:
                    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    text = child.text
                    
                    if tag == 'shrsOrPrnAmt':
                        # Handle nested structure
                        ssh_prnamt = child.find('info:sshPrnamt', ns)
                        if ssh_prnamt is None:
                            ssh_prnamt = child.find('.//info:sshPrnamt', ns)
                        if ssh_prnamt is not None and ssh_prnamt.text:
                            try:
                                shares_text = ssh_prnamt.text.replace(',', '').strip()
                                holding['shares'] = int(float(shares_text))
                            except:
                                holding['shares'] = ssh_prnamt.text
                        ssh_prnamt_type = child.find('info:sshPrnamtType', ns)
                        if ssh_prnamt_type is None:
                            ssh_prnamt_type = child.find('.//info:sshPrnamtType', ns)
                        if ssh_prnamt_type is not None:
                            holding['sharesType'] = ssh_prnamt_type.text
                    elif tag == 'value':
                        if text:
                            text = text.replace(',', '').replace('$', '').strip()
                            try:
                                holding[tag] = int(float(text) * 100)  # Convert to cents
                            except:
                                holding[tag] = text
                    elif tag == 'votingAuthority':
                        # Handle nested voting authority
                        for vote_child in child:
                            vote_tag = vote_child.tag.split('}')[-1] if '}' in vote_child.tag else vote_child.tag
                            holding[f'voting_{vote_tag.lower()}'] = vote_child.text
                    else:
                        holding[tag] = text
                
                holdings.append(holding)
            
            return {
                'header': header_info,
                'period_end': period_end,
                'holdings': holdings
            }
        except Exception as e:
            print(f"Error parsing informationTable XML: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def holdings_to_csv(self, holdings: List[Dict[str, Any]]) -> str:
        """Convert holdings list to CSV string"""
        if not holdings:
            return ""
        
        # Get all unique keys from holdings
        all_keys = set()
        for holding in holdings:
            all_keys.update(holding.keys())
        
        # Standardize column names
        columns = sorted(all_keys)
        
        # Create CSV
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        
        for holding in holdings:
            writer.writerow(holding)
        
        return output.getvalue()
    
    def save_to_minio(self, cik: str, quarter: str, accession_number: str, csv_content: str, form_type: str) -> str:
        """Save CSV to MinIO and return path"""
        self._ensure_bucket_exists()
        
        # Path format: 13f/{cik}/{quarter}/{accession_number}.csv
        file_path = f"13f/{cik}/{quarter}/{accession_number}.csv"
        
        client = self._get_minio_client()
        client.put_object(
            Bucket=self.minio_bucket,
            Key=file_path,
            Body=csv_content.encode('utf-8'),
            ContentType='text/csv'
        )
        
        return file_path
    
    def process_filing(self, db: Session, filing_data: Dict[str, Any], force_reprocess: bool = False) -> bool:
        """
        Process a single 13F filing:
        1. Check if already processed
        2. Fetch and parse filing
        3. Generate CSV
        4. Save to MinIO
        5. Store metadata in database
        """
        cik = filing_data['cik']
        accession_number = filing_data['accession_number']
        form_type = filing_data['form_type']
        filing_date = filing_data['filing_date']
        
        # Check if already processed
        existing = db.query(Filing13F).filter(
            Filing13F.accession_number == accession_number
        ).first()
        
        if existing and not force_reprocess:
            # Check if this is an amended filing that should override
            if form_type == '13F-HR/A' and existing.form_type == '13F-HR':
                # Amended filing - reprocess
                print(f"Processing amended filing {accession_number} (overriding {existing.accession_number})")
            elif form_type == '13F-NT':
                # No holdings table - just mark as processed
                print(f"Skipping 13F-NT filing {accession_number} (no holdings)")
                if not existing:
                    db_filing = Filing13F(
                        cik=cik,
                        accession_number=accession_number,
                        form_type=form_type,
                        filing_date=filing_date,
                        period_end_date=filing_date,  # Use filing date as fallback
                        quarter=self.get_quarter_from_date(filing_date),
                        is_amended=False,
                        holdings_count=0
                    )
                    db.add(db_filing)
                    db.commit()
                return True
            else:
                print(f"Filing {accession_number} already processed, skipping")
                return False
        
        # Skip 13F-NT (no holdings table)
        if form_type == '13F-NT':
            print(f"Skipping 13F-NT filing {accession_number} (no holdings table)")
            if not existing:
                db_filing = Filing13F(
                    cik=cik,
                    accession_number=accession_number,
                    form_type=form_type,
                    filing_date=filing_date,
                    period_end_date=filing_date,
                    quarter=self.get_quarter_from_date(filing_date),
                    is_amended=False,
                    holdings_count=0
                )
                db.add(db_filing)
                db.commit()
            return True
        
        # Fetch filing content
        filing_data = self.get_filing_content(cik, accession_number)
        if not filing_data:
            print(f"Could not fetch content for filing {accession_number}")
            return False
        
        # Handle both dict (with separate XML) and string (embedded XML) formats
        if isinstance(filing_data, dict):
            content = filing_data['main']
            xml_file_content = filing_data.get('xml')
        else:
            content = filing_data
            xml_file_content = None
        
        # Parse XML
        parsed = self.parse_13f_xml(content, xml_file_content)
        if not parsed or not parsed.get('holdings'):
            print(f"Could not parse holdings from filing {accession_number}")
            return False
        
        holdings = parsed['holdings']
        period_end = parsed.get('period_end') or filing_date
        quarter = self.get_quarter_from_date(period_end)
        
        # Enrich holdings with ticker/company info from CUSIP
        holdings = self.enrich_holdings_with_tickers(holdings)
        
        # Generate CSV
        csv_content = self.holdings_to_csv(holdings)
        if not csv_content:
            print(f"No holdings data to save for filing {accession_number}")
            return False
        
        # Save to MinIO
        minio_path = self.save_to_minio(cik, quarter, accession_number, csv_content, form_type)
        
        # Calculate total value
        total_value = sum(h.get('value', 0) for h in holdings if isinstance(h.get('value'), int))
        
        # Save to database
        if existing:
            # Update existing record (for amended filings)
            existing.form_type = form_type
            existing.filing_date = filing_date
            existing.period_end_date = period_end
            existing.quarter = quarter
            existing.is_amended = (form_type == '13F-HR/A')
            existing.minio_path = minio_path
            existing.holdings_count = len(holdings)
            existing.total_value = total_value
            existing.updated_at = datetime.now()
        else:
            db_filing = Filing13F(
                cik=cik,
                accession_number=accession_number,
                form_type=form_type,
                filing_date=filing_date,
                period_end_date=period_end,
                quarter=quarter,
                is_amended=(form_type == '13F-HR/A'),
                minio_path=minio_path,
                holdings_count=len(holdings),
                total_value=total_value
            )
            db.add(db_filing)
        
        db.commit()
        print(f"Processed filing {accession_number} for CIK {cik}: {len(holdings)} holdings")
        return True
    
    def get_last_processed_accession(self, db: Session, cik: str) -> Optional[str]:
        """Get the last processed accession number for a CIK"""
        last_filing = db.query(Filing13F).filter(
            Filing13F.cik == cik
        ).order_by(Filing13F.filing_date.desc()).first()
        
        return last_filing.accession_number if last_filing else None
    
    def compare_quarters(self, db: Session, cik: str, current_quarter: str, prior_quarter: str, 
                        min_change_pct: float = 5.0) -> Dict[str, Any]:
        """
        Compare holdings between two quarters and identify:
        - New positions (BUY)
        - Closed positions (SELL)
        - Size changes > X%
        """
        # Get filings for both quarters
        current_filing = db.query(Filing13F).filter(
            and_(
                Filing13F.cik == cik,
                Filing13F.quarter == current_quarter,
                Filing13F.form_type.in_(['13F-HR', '13F-HR/A'])
            )
        ).order_by(Filing13F.filing_date.desc()).first()
        
        prior_filing = db.query(Filing13F).filter(
            and_(
                Filing13F.cik == cik,
                Filing13F.quarter == prior_quarter,
                Filing13F.form_type.in_(['13F-HR', '13F-HR/A'])
            )
        ).order_by(Filing13F.filing_date.desc()).first()
        
        if not current_filing or not prior_filing:
            return {
                'error': 'Missing filings for comparison',
                'current_quarter': current_quarter,
                'prior_quarter': prior_quarter
            }
        
        # Load holdings from MinIO
        current_holdings = self._load_holdings_from_minio(current_filing.minio_path)
        prior_holdings = self._load_holdings_from_minio(prior_filing.minio_path)
        
        if not current_holdings or not prior_holdings:
            return {
                'error': 'Could not load holdings from MinIO',
                'current_quarter': current_quarter,
                'prior_quarter': prior_quarter
            }
        
        # Convert value strings to int (they're stored as cents)
        def parse_value(v):
            if isinstance(v, str):
                try:
                    return int(float(v))
                except:
                    return 0
            return int(v) if v else 0
        
        def parse_shares(v):
            if isinstance(v, str):
                try:
                    return int(float(v.replace(',', '')))
                except:
                    return 0
            return int(v) if v else 0
        
        # Create CUSIP index
        current_by_cusip = {h.get('cusip', ''): h for h in current_holdings if h.get('cusip')}
        prior_by_cusip = {h.get('cusip', ''): h for h in prior_holdings if h.get('cusip')}
        
        # Find new positions (BUY)
        new_positions = []
        for cusip in current_by_cusip.keys():
            if cusip not in prior_by_cusip:
                holding = current_by_cusip[cusip].copy()
                holding['action'] = 'BUY'
                holding['shares_change'] = parse_shares(holding.get('shares', holding.get('sshPrnamt', 0)))
                holding['value_change'] = parse_value(holding.get('value', 0))
                new_positions.append(holding)
        
        # Find closed positions (SELL)
        closed_positions = []
        for cusip in prior_by_cusip.keys():
            if cusip not in current_by_cusip:
                holding = prior_by_cusip[cusip].copy()
                holding['action'] = 'SELL'
                holding['shares_change'] = -parse_shares(holding.get('shares', holding.get('sshPrnamt', 0)))
                holding['value_change'] = -parse_value(holding.get('value', 0))
                closed_positions.append(holding)
        
        # Find size changes
        size_changes = []
        for cusip in current_by_cusip.keys():
            if cusip in prior_by_cusip:
                current_holding = current_by_cusip[cusip]
                prior_holding = prior_by_cusip[cusip]
                
                current_value = parse_value(current_holding.get('value', 0))
                prior_value = parse_value(prior_holding.get('value', 0))
                current_shares = parse_shares(current_holding.get('shares', current_holding.get('sshPrnamt', 0)))
                prior_shares = parse_shares(prior_holding.get('shares', prior_holding.get('sshPrnamt', 0)))
                
                if prior_value > 0:
                    change_pct = ((current_value - prior_value) / prior_value) * 100
                    if abs(change_pct) >= min_change_pct:
                        action = 'BUY' if current_shares > prior_shares else 'SELL'
                        size_changes.append({
                            'cusip': cusip,
                            'ticker': current_holding.get('ticker', ''),
                            'nameOfIssuer': current_holding.get('nameOfIssuer', current_holding.get('companyName', '')),
                            'companyName': current_holding.get('companyName', ''),
                            'prior_value': prior_value,
                            'current_value': current_value,
                            'value_change': current_value - prior_value,
                            'change_pct': change_pct,
                            'prior_shares': prior_shares,
                            'current_shares': current_shares,
                            'shares_change': current_shares - prior_shares,
                            'action': action
                        })
        
        return {
            'cik': cik,
            'current_quarter': current_quarter,
            'prior_quarter': prior_quarter,
            'new_positions': new_positions,
            'closed_positions': closed_positions,
            'size_changes': size_changes,
            'new_positions_count': len(new_positions),
            'closed_positions_count': len(closed_positions),
            'size_changes_count': len(size_changes)
        }
    
    def get_institution_holdings_by_ticker(self, db: Session, ticker: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all institution holdings for a specific ticker, with buy/sell indicators.
        Returns list of holdings with institution info and quarter-over-quarter changes.
        """
        # First, get all holdings for this ticker from all processed filings
        # We need to search through all MinIO files
        all_holdings = []
        
        # Get all filings
        filings = db.query(Filing13F).filter(
            Filing13F.form_type.in_(['13F-HR', '13F-HR/A'])
        ).order_by(Filing13F.filing_date.desc()).limit(1000).all()  # Limit to recent filings
        
        for filing in filings:
            holdings = self._load_holdings_from_minio(filing.minio_path)
            # Filter by ticker OR by company name (fallback for holdings without ticker mapping)
            ticker_holdings = []
            for h in holdings:
                holding_ticker = h.get('ticker', '').upper()
                holding_issuer = h.get('nameOfIssuer', '').upper()
                holding_company = h.get('companyName', '').upper()
                
                # Match by ticker
                if holding_ticker == ticker.upper():
                    ticker_holdings.append(h)
                # Fallback: match by company name (e.g., "TESLA INC" for "TSLA")
                elif not holding_ticker:
                    # Try to match common company name patterns
                    ticker_to_name_map = {
                        'TSLA': ['TESLA'],
                        'AAPL': ['APPLE'],
                        'MSFT': ['MICROSOFT'],
                        'GOOGL': ['GOOGLE', 'ALPHABET'],
                        'AMZN': ['AMAZON'],
                        'META': ['META', 'FACEBOOK'],
                        'NVDA': ['NVIDIA'],
                        'JPM': ['JPMORGAN', 'JP MORGAN'],
                        'BAC': ['BANK OF AMERICA'],
                        'WMT': ['WALMART']
                    }
                    
                    if ticker.upper() in ticker_to_name_map:
                        for name_pattern in ticker_to_name_map[ticker.upper()]:
                            if name_pattern in holding_issuer or name_pattern in holding_company:
                                ticker_holdings.append(h)
                                break
            
            for holding in ticker_holdings:
                # Get institution info from CIK
                institution_name = self._get_institution_name(filing.cik)
                
                # Calculate change from prior quarter
                prior_quarter = self._get_prior_quarter(filing.quarter)
                prior_filing = db.query(Filing13F).filter(
                    and_(
                        Filing13F.cik == filing.cik,
                        Filing13F.quarter == prior_quarter,
                        Filing13F.form_type.in_(['13F-HR', '13F-HR/A'])
                    )
                ).order_by(Filing13F.filing_date.desc()).first()
                
                action = 'HOLD'
                shares_change = 0
                value_change = 0
                change_pct = 0
                
                if prior_filing:
                    prior_holdings = self._load_holdings_from_minio(prior_filing.minio_path)
                    # Match by CUSIP (most reliable) or by ticker if available
                    prior_holding = None
                    holding_cusip = holding.get('cusip', '')
                    if holding_cusip:
                        # First try to match by CUSIP (most reliable)
                        prior_holding = next((h for h in prior_holdings if h.get('cusip') == holding_cusip), None)
                    if not prior_holding:
                        # Fallback: match by ticker or company name
                        prior_holding = next((h for h in prior_holdings 
                                            if (h.get('ticker', '').upper() == ticker.upper() or
                                                (not h.get('ticker') and 'TESLA' in h.get('nameOfIssuer', '').upper()))), None)
                    
                    if prior_holding:
                        current_shares = int(float(str(holding.get('shares', holding.get('sshPrnamt', 0))).replace(',', '')))
                        prior_shares = int(float(str(prior_holding.get('shares', prior_holding.get('sshPrnamt', 0))).replace(',', '')))
                        current_value = int(float(str(holding.get('value', 0)).replace(',', '')))
                        prior_value = int(float(str(prior_holding.get('value', 0)).replace(',', '')))
                        
                        shares_change = current_shares - prior_shares
                        value_change = current_value - prior_value
                        
                        if shares_change > 0:
                            action = 'BUY'
                        elif shares_change < 0:
                            action = 'SELL'
                        
                        if prior_value > 0:
                            change_pct = ((current_value - prior_value) / prior_value) * 100
                    else:
                        # New position
                        action = 'BUY'
                        shares_change = int(float(str(holding.get('shares', holding.get('sshPrnamt', 0))).replace(',', '')))
                        value_change = int(float(str(holding.get('value', 0)).replace(',', '')))
                else:
                    # First filing for this institution
                    action = 'NEW'
                    shares_change = int(float(str(holding.get('shares', holding.get('sshPrnamt', 0))).replace(',', '')))
                    value_change = int(float(str(holding.get('value', 0)).replace(',', '')))
                
                all_holdings.append({
                    'Date Reported': filing.period_end_date.isoformat() if filing.period_end_date else filing.filing_date.isoformat(),
                    'Holder': institution_name,
                    'Shares': int(float(str(holding.get('shares', holding.get('sshPrnamt', 0))).replace(',', ''))),
                    'Value': int(float(str(holding.get('value', 0)).replace(',', ''))) / 100,  # Convert from cents to dollars
                    'pctHeld': 0,  # Would need total shares outstanding to calculate
                    'pctChange': change_pct,
                    'action': action,
                    'sharesChange': shares_change,
                    'valueChange': value_change / 100,  # Convert from cents to dollars
                    'cusip': holding.get('cusip', ''),
                    'ticker': holding.get('ticker', ticker),
                    'companyName': holding.get('companyName', holding.get('nameOfIssuer', '')),
                    'quarter': filing.quarter,
                    'cik': filing.cik
                })
        
        # Sort by date (most recent first), then by value
        all_holdings.sort(key=lambda x: (x['Date Reported'], -x['Value']), reverse=True)
        
        return all_holdings[:limit]
    
    def _get_institution_name(self, cik: str) -> str:
        """Get institution name from CIK"""
        try:
            url = f"https://data.sec.gov/submissions/CIK{cik.zfill(10)}.json"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('name', f'CIK {cik}')
        except:
            pass
        return f'CIK {cik}'
    
    def _get_prior_quarter(self, quarter: str) -> str:
        """Get the prior quarter string"""
        year, q = quarter.split('-')
        year = int(year)
        if q == 'Q1':
            return f"{year - 1}-Q4"
        elif q == 'Q2':
            return f"{year}-Q1"
        elif q == 'Q3':
            return f"{year}-Q2"
        else:  # Q4
            return f"{year}-Q3"
    
    def _load_holdings_from_minio(self, minio_path: str) -> List[Dict[str, Any]]:
        """Load holdings CSV from MinIO"""
        try:
            client = self._get_minio_client()
            response = client.get_object(Bucket=self.minio_bucket, Key=minio_path)
            content = response['Body'].read().decode('utf-8')
            
            # Parse CSV
            reader = csv.DictReader(io.StringIO(content))
            return list(reader)
        except Exception as e:
            print(f"Error loading holdings from MinIO {minio_path}: {e}")
            return []
    
    def get_ticker_from_cusip(self, cusip: str) -> Optional[Dict[str, Any]]:
        """
        Map CUSIP to ticker/company using SEC Security API.
        Returns dict with ticker, companyName, or None if not found.
        """
        if not cusip or len(cusip) < 6:
            return None
        
        # Check cache first
        if cusip in self.cusip_cache:
            return self.cusip_cache[cusip]
        
        try:
            # Use CUSIP-6 (first 6 digits) for search
            cusip6 = cusip[:6]
            
            # SEC API endpoint for security lookup
            # Try CUSIP-9 first, then CUSIP-6
            for cusip_to_try in [cusip, cusip6]:
                url = f"https://data.sec.gov/api/xbrl/security/{cusip_to_try}"
                try:
                    response = requests.get(url, headers=self.headers, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        # Extract ticker and company name
                        result = {
                            'ticker': data.get('ticker', ''),
                            'companyName': data.get('entityName', ''),
                            'cusip': cusip,
                            'securityName': data.get('securityName', '')
                        }
                        # Cache the result
                        self.cusip_cache[cusip] = result
                        return result
                    elif response.status_code == 404:
                        # Not found, try next
                        continue
                except Exception as e:
                    print(f"Error fetching CUSIP {cusip_to_try} from SEC API: {e}")
                    continue
            
            # Not found in SEC API
            self.cusip_cache[cusip] = None
            return None
            
        except Exception as e:
            print(f"Error mapping CUSIP {cusip} to ticker: {e}")
            return None
    
    def enrich_holdings_with_tickers(self, holdings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enrich holdings with ticker and company name from CUSIP"""
        enriched = []
        for holding in holdings:
            cusip = holding.get('cusip', '')
            if cusip:
                ticker_info = self.get_ticker_from_cusip(cusip)
                if ticker_info:
                    holding['ticker'] = ticker_info.get('ticker', '')
                    holding['companyName'] = ticker_info.get('companyName', '')
                    holding['securityName'] = ticker_info.get('securityName', '')
                else:
                    holding['ticker'] = ''
                    holding['companyName'] = holding.get('nameOfIssuer', '')  # Fallback to nameOfIssuer
                    holding['securityName'] = ''
            else:
                holding['ticker'] = ''
                holding['companyName'] = holding.get('nameOfIssuer', '')
                holding['securityName'] = ''
            
            enriched.append(holding)
        
        return enriched
    
    def process_batch(self, db: Session, quarters: Optional[List[str]] = None, 
                     force_reprocess: bool = False) -> Dict[str, Any]:
        """
        Process 13F filings in batch for specified quarters.
        If quarters not specified, process current and prior quarter.
        """
        if not quarters:
            # Default to current and prior quarter
            now = datetime.now()
            current_quarter = self.get_quarter_from_date(now)
            # Get prior quarter
            if now.month <= 3:
                prior_quarter = f"{now.year - 1}-Q4"
            elif now.month <= 6:
                prior_quarter = f"{now.year}-Q1"
            elif now.month <= 9:
                prior_quarter = f"{now.year}-Q2"
            else:
                prior_quarter = f"{now.year}-Q3"
            quarters = [current_quarter, prior_quarter]
        
        # Calculate date range
        start_date = None
        end_date = None
        for quarter in quarters:
            year, q = quarter.split("-")
            year = int(year)
            if q == "Q1":
                q_start = datetime(year, 1, 1)
                q_end = datetime(year, 3, 31)
            elif q == "Q2":
                q_start = datetime(year, 4, 1)
                q_end = datetime(year, 6, 30)
            elif q == "Q3":
                q_start = datetime(year, 7, 1)
                q_end = datetime(year, 9, 30)
            else:  # Q4
                q_start = datetime(year, 10, 1)
                q_end = datetime(year, 12, 31)
            
            if start_date is None or q_start < start_date:
                start_date = q_start
            if end_date is None or q_end > end_date:
                end_date = q_end
        
        # Get all 13F filings in date range
        filings = self.get_all_13f_filings(start_date, end_date)
        
        # Filter by quarters
        quarter_filings = []
        for filing in filings:
            filing_quarter = self.get_quarter_from_date(filing['filing_date'])
            if filing_quarter in quarters:
                quarter_filings.append(filing)
        
        # Process each filing
        processed = 0
        skipped = 0
        errors = 0
        
        for filing in quarter_filings:
            try:
                if self.process_filing(db, filing, force_reprocess):
                    processed += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"Error processing filing {filing['accession_number']}: {e}")
                errors += 1
        
        return {
            'quarters': quarters,
            'total_filings': len(quarter_filings),
            'processed': processed,
            'skipped': skipped,
            'errors': errors
        }


# Global instance
filing_13f_service = Filing13FService()

