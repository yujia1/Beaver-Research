import requests
import json
import os
from typing import Optional, Dict, List, Any
import datetime
from bs4 import BeautifulSoup
import re

class EdgarService:
    """
    Service to interact with SEC EDGAR API.
    """
    def __init__(self):
        # SEC requires a User-Agent with contact info (email)
        self.headers = {
            "User-Agent": "FinancialDashboard contact@example.com"  # Replace with valid email in prod
        }
        self.cik_map = {}
        self._load_cik_map()

    def _load_cik_map(self):
        """Load ticker -> CIK mapping from SEC bulk data."""
        try:
            url = "https://www.sec.gov/files/company_tickers.json"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Data format: {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ...}
                for entry in data.values():
                    self.cik_map[entry["ticker"]] = str(entry["cik_str"]).zfill(10)
        except Exception as e:
            print(f"Error loading CIK map: {e}")

    def get_cik(self, ticker: str) -> Optional[str]:
        """Get CIK for a ticker."""
        return self.cik_map.get(ticker.upper())

    def get_company_submissions(self, ticker: str) -> Dict[str, Any]:
        """Get company submissions including recent filings."""
        cik = self.get_cik(ticker)
        if not cik:
            # Try to reload map if not found
            self._load_cik_map()
            cik = self.get_cik(ticker)
            if not cik:
                return {"error": "CIK not found"}

        try:
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            return {"error": f"SEC API returned {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    def get_institutional_holdings(self, ticker: str) -> List[Dict[str, Any]]:
        """
        Get institutional holdings from 13F filings.
        Note: SEC API provides raw filings. Parsing 13F XML/Text is complex.
        For this simplified version, we'll look for 13F-HR filings in submissions
        and return metadata, as parsing full holdings requires processing the primary document.
        """
        data = self.get_company_submissions(ticker)
        if "error" in data:
            return []

        filings = data.get("filings", {}).get("recent", {})
        if not filings:
            return []

        forms = filings.get("form", [])
        dates = filings.get("filingDate", [])
        accession_numbers = filings.get("accessionNumber", [])
        primary_docs = filings.get("primaryDocument", [])

        holdings_filings = []
        for i, form in enumerate(forms):
            if form in ["13F-HR", "13F-NT", "13D", "13G", "SC 13D", "SC 13G"]:
                accession = accession_numbers[i].replace("-", "")
                primary_doc = primary_docs[i]
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{data['cik']}/{accession}/{primary_doc}"
                
                holdings_filings.append({
                    "form": form,
                    "date": dates[i],
                    "link": filing_url,
                    "description": f"Institutional/Beneficial Ownership Filing ({form})"
                })
        
        return holdings_filings

    def _extract_section_text(self, element) -> str:
        """Extract and clean text from an HTML element."""
        if element is None:
            return ""
        
        text = element.get_text(separator='\n', strip=True)
        # Clean up the text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        return text.strip()

    def _find_section(self, soup: BeautifulSoup, patterns: List[str], max_length: int = 50000) -> str:
        """
        Find a section in the 10-K by searching for various patterns.
        Returns the text content of the section.
        """
        text_content = soup.get_text()
        
        for pattern in patterns:
            # Try to find the section using regex
            # Look for patterns like "Item 1.", "ITEM 1", "Item 1A", etc.
            # Escape the pattern and create regex that matches until next Item or PART
            escaped_pattern = re.escape(pattern)
            regex_patterns = [
                rf"{escaped_pattern}.*?(?=(?:Item\s+\d+[A-Z]?\.|PART\s+[IVX]+|$))",
                rf"{escaped_pattern}.*",
            ]
            
            for regex_pattern in regex_patterns:
                try:
                    match = re.search(regex_pattern, text_content, re.DOTALL | re.IGNORECASE)
                    if match:
                        section_text = match.group(0)
                        # Clean up
                        section_text = re.sub(r'\n{3,}', '\n\n', section_text)
                        section_text = re.sub(r' +', ' ', section_text)
                        
                        # Truncate if too long
                        if len(section_text) > max_length:
                            section_text = section_text[:max_length] + "\n\n[Section truncated due to length...]"
                        
                        return section_text.strip()
                except re.error as e:
                    # Skip invalid regex patterns
                    print(f"Regex error for pattern '{pattern}': {e}")
                    continue
        
        return ""

    def get_latest_10k_content(self, ticker: str, max_chunk_length: int = 50000) -> Optional[Dict[str, str]]:
        """
        Fetch the latest 10-K filing and extract specific chunks.
        Returns a dictionary with chunks:
        - chunk_a: Item 1. Business
        - chunk_b: Item 1A. Risk Factors
        - chunk_c1: Item 7. MD&A
        - chunk_c2: Item 7A. Market Risk
        - chunk_d: Item 8. Financial Statements
        - chunk_e: Items 10, 11, 12, (optionally 13) - Governance, Compensation, Ownership
        """
        cik = self.get_cik(ticker)
        if not cik:
            self._load_cik_map()
            cik = self.get_cik(ticker)
            if not cik:
                return None

        try:
            submissions = self.get_company_submissions(ticker)
            if "error" in submissions:
                return None

            filings = submissions.get("filings", {}).get("recent", {})
            if not filings:
                return None

            forms = filings.get("form", [])
            dates = filings.get("filingDate", [])
            accession_numbers = filings.get("accessionNumber", [])
            primary_docs = filings.get("primaryDocument", [])

            # Find the latest 10-K
            latest_10k_index = None
            latest_date = None
            for i, form in enumerate(forms):
                if form == "10-K":
                    filing_date = dates[i]
                    if latest_date is None or filing_date > latest_date:
                        latest_date = filing_date
                        latest_10k_index = i

            if latest_10k_index is None:
                return None

            # Get the filing URL
            accession = accession_numbers[latest_10k_index].replace("-", "")
            primary_doc = primary_docs[latest_10k_index]
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary_doc}"

            # Fetch the filing content
            response = requests.get(filing_url, headers=self.headers, timeout=30)
            if response.status_code != 200:
                return None

            # Parse HTML
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get full text for pattern matching
            full_text = soup.get_text()
            
            # Define section patterns to search for
            chunks = {}
            
            # Chunk A - Item 1. Business
            chunk_a_patterns = [
                "Item 1.", "ITEM 1.", "Item 1 ", "ITEM 1 ", 
                "PART I\nItem 1.", "PART I\nITEM 1."
            ]
            chunks["chunk_a"] = self._find_section(soup, chunk_a_patterns, max_chunk_length)
            
            # Chunk B - Item 1A. Risk Factors
            chunk_b_patterns = [
                "Item 1A.", "ITEM 1A.", "Item 1A ", "ITEM 1A ",
                "Risk Factors", "RISK FACTORS"
            ]
            chunks["chunk_b"] = self._find_section(soup, chunk_b_patterns, max_chunk_length)
            
            # Chunk C1 - Item 7. MD&A
            chunk_c1_patterns = [
                "Item 7.", "ITEM 7.", "Item 7 ", "ITEM 7 ",
                "Management's Discussion", "MANAGEMENT'S DISCUSSION",
                "MD&A", "Management Discussion and Analysis"
            ]
            chunks["chunk_c1"] = self._find_section(soup, chunk_c1_patterns, max_chunk_length)
            
            # Chunk C2 - Item 7A. Market Risk
            chunk_c2_patterns = [
                "Item 7A.", "ITEM 7A.", "Item 7A ", "ITEM 7A ",
                "Quantitative and Qualitative Disclosures about Market Risk",
                "Market Risk"
            ]
            chunks["chunk_c2"] = self._find_section(soup, chunk_c2_patterns, max_chunk_length)
            
            # Chunk D - Item 8. Financial Statements
            chunk_d_patterns = [
                "Item 8.", "ITEM 8.", "Item 8 ", "ITEM 8 ",
                "Financial Statements and Supplementary Data",
                "FINANCIAL STATEMENTS"
            ]
            chunks["chunk_d"] = self._find_section(soup, chunk_d_patterns, max_chunk_length)
            
            # Chunk E - Items 10, 11, 12, (optionally 13)
            chunk_e_patterns = [
                "Item 10.", "ITEM 10.", "Directors, Executive Officers",
                "Item 11.", "ITEM 11.", "Executive Compensation",
                "Item 12.", "ITEM 12.", "Security Ownership",
                "Item 13.", "ITEM 13.", "Certain Relationships"
            ]
            chunks["chunk_e"] = self._find_section(soup, chunk_e_patterns, max_chunk_length * 2)  # Allow more length for combined items
            
            # If pattern matching didn't work well, try a more aggressive approach
            # Split the document by common section markers and extract relevant parts
            if not any(chunks.values()):
                print(f"Warning: Pattern matching failed for {ticker}, trying alternative extraction method...")
                # Fallback: try to find sections by looking for table of contents or section headers
                # This is a simplified fallback - in production, you might want more sophisticated parsing
                text_lines = full_text.split('\n')
                current_section = None
                section_content = {}
                
                for i, line in enumerate(text_lines):
                    line_upper = line.upper().strip()
                    
                    # Detect section starts
                    if re.search(r'(?i)^(Item\s+)?1\.?\s+(Business|BUSINESS)', line):
                        current_section = 'chunk_a'
                        section_content[current_section] = []
                    elif re.search(r'(?i)^(Item\s+)?1A\.?\s+(Risk|RISK)', line):
                        current_section = 'chunk_b'
                        section_content[current_section] = []
                    elif re.search(r'(?i)^(Item\s+)?7\.?\s+(Management|MD&A)', line):
                        current_section = 'chunk_c1'
                        section_content[current_section] = []
                    elif re.search(r'(?i)^(Item\s+)?7A\.?\s+(Market|MARKET)', line):
                        current_section = 'chunk_c2'
                        section_content[current_section] = []
                    elif re.search(r'(?i)^(Item\s+)?8\.?\s+(Financial|FINANCIAL)', line):
                        current_section = 'chunk_d'
                        section_content[current_section] = []
                    elif re.search(r'(?i)^(Item\s+)?(10|11|12|13)\.?\s+', line):
                        if current_section != 'chunk_e':
                            current_section = 'chunk_e'
                            section_content[current_section] = []
                    
                    # Stop at next major section (Item X or PART)
                    if current_section and re.search(r'(?i)^(Item\s+\d+[A-Z]?\.|PART\s+[IVX]+)', line):
                        # Check if this is a new major section that's not part of current chunk
                        if current_section == 'chunk_e' and re.search(r'(?i)^(Item\s+)?(10|11|12|13)\.', line):
                            # Continue adding to chunk_e
                            pass
                        elif not (current_section == 'chunk_e' and re.search(r'(?i)^(Item\s+)?(10|11|12|13)\.', line)):
                            # This is a new section, stop current one
                            if current_section in section_content:
                                content = '\n'.join(section_content[current_section])
                                if len(content) > max_chunk_length:
                                    content = content[:max_chunk_length] + "\n\n[Section truncated...]"
                                chunks[current_section] = content
                            current_section = None
                    
                    # Add line to current section
                    if current_section:
                        section_content.setdefault(current_section, []).append(line)
                
                # Finalize last section
                if current_section and current_section in section_content:
                    content = '\n'.join(section_content[current_section])
                    if len(content) > max_chunk_length:
                        content = content[:max_chunk_length] + "\n\n[Section truncated...]"
                    chunks[current_section] = content

            return chunks

        except Exception as e:
            print(f"Error fetching 10-K content for {ticker}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_latest_10k_full(self, ticker: str) -> Optional[str]:
        """
        Fetch the latest 10-K filing and return the HTML content.
        Returns the complete 10-K document as HTML to preserve original formatting.
        """
        cik = self.get_cik(ticker)
        if not cik:
            self._load_cik_map()
            cik = self.get_cik(ticker)
            if not cik:
                return None

        try:
            submissions = self.get_company_submissions(ticker)
            if "error" in submissions:
                return None

            filings = submissions.get("filings", {}).get("recent", {})
            if not filings:
                return None

            forms = filings.get("form", [])
            dates = filings.get("filingDate", [])
            accession_numbers = filings.get("accessionNumber", [])
            primary_docs = filings.get("primaryDocument", [])

            # Find the latest 10-K
            latest_10k_index = None
            latest_date = None
            for i, form in enumerate(forms):
                if form == "10-K":
                    filing_date = dates[i]
                    if latest_date is None or filing_date > latest_date:
                        latest_date = filing_date
                        latest_10k_index = i

            if latest_10k_index is None:
                return None

            # Get the filing URL
            accession = accession_numbers[latest_10k_index].replace("-", "")
            primary_doc = primary_docs[latest_10k_index]
            filing_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primary_doc}"

            # Fetch the filing content
            response = requests.get(filing_url, headers=self.headers, timeout=30)
            if response.status_code != 200:
                return None

            # Parse HTML
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Remove unwanted elements that don't contribute to readable content
            # But keep HTML structure for formatting
            for element in soup.find_all(['script', 'style', 'noscript']):
                element.decompose()
            
            # Remove XBRL-related elements (they often have specific attributes or are in specific tags)
            for element in soup.find_all(attrs={'class': re.compile(r'xbrl|xml', re.I)}):
                element.decompose()
            
            # Remove elements with XBRL-related IDs
            for element in soup.find_all(id=re.compile(r'xbrl|xml', re.I)):
                element.decompose()
            
            # Remove hidden elements
            for element in soup.find_all(attrs={'style': re.compile(r'display:\s*none|visibility:\s*hidden', re.I)}):
                element.decompose()
            
            # Remove meta and link tags (they don't display content)
            for element in soup.find_all(['meta', 'link']):
                element.decompose()
            
            # Clean up inline XBRL attributes from remaining elements
            # Remove XBRL-related attributes but keep the elements
            for element in soup.find_all(True):
                # Remove XBRL namespace attributes
                attrs_to_remove = []
                for attr in element.attrs:
                    if 'xbrl' in attr.lower() or 'xmlns' in attr.lower():
                        attrs_to_remove.append(attr)
                for attr in attrs_to_remove:
                    del element.attrs[attr]
            
            # Try to find the main document content
            # SEC filings often have the content in specific divs or tables
            main_content = None
            
            # Look for common SEC filing content containers
            content_selectors = [
                {'class': re.compile(r'document|filing|content|text', re.I)},
                {'id': re.compile(r'document|filing|content|text', re.I)},
            ]
            
            for selector in content_selectors:
                main_content = soup.find('div', selector)
                if main_content:
                    break
            
            # If no specific container found, use the body content
            if not main_content:
                main_content = soup.find('body')
                if not main_content:
                    main_content = soup
            
            # Get the HTML string from the main content
            html_content = str(main_content)
            
            # Clean up some XBRL artifacts that might be in text nodes
            # But preserve HTML structure
            html_content = re.sub(r'<[^>]*xbrl[^>]*>', '', html_content, flags=re.I)
            html_content = re.sub(r'xmlns[^=]*="[^"]*"', '', html_content)
            
            return html_content

        except Exception as e:
            print(f"Error fetching full 10-K content for {ticker}: {e}")
            import traceback
            traceback.print_exc()
            return None

edgar_service = EdgarService()



