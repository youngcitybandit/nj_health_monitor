"""
Web scraper for NJ Health Facility Enforcement Actions website.
Handles scraping the main page and downloading PDFs.
"""

import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
import os
import hashlib

logger = logging.getLogger(__name__)

class NJHealthScraper:
    """Scraper for the NJ Health Facility Enforcement Actions website."""
    
    def __init__(self):
        self.base_url = "https://www.nj.gov/health/healthfacilities/surveys-insp/enforcement_actions.shtml"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.last_check_file = "last_check.txt"
        
    def get_page_content(self):
        """Fetch the main page content."""
        try:
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching page content: {str(e)}")
            raise
    
    def parse_entries(self, html_content):
        """Parse the HTML content to extract enforcement action entries."""
        soup = BeautifulSoup(html_content, 'html.parser')
        entries = []
        
        # Find the table containing enforcement actions
        table = soup.find('table')
        if not table:
            logger.warning("No table found on the page")
            return entries
        
        # Parse table rows
        rows = table.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 3:
                try:
                    date_str = cells[0].get_text(strip=True)
                    facility_name_cell = cells[1]
                    enforcement_action = cells[2].get_text(strip=True)
                    
                    # Extract facility name and PDF URL
                    facility_link = facility_name_cell.find('a')
                    if facility_link:
                        facility_name = facility_link.get_text(strip=True)
                        pdf_url = facility_link.get('href')
                        
                        # Convert relative URL to absolute
                        if pdf_url and not pdf_url.startswith('http'):
                            pdf_url = urljoin(self.base_url, pdf_url)
                        
                        # Parse date
                        try:
                            entry_date = datetime.strptime(date_str, '%m/%d/%Y')
                        except ValueError:
                            logger.warning(f"Could not parse date: {date_str}")
                            continue
                        
                        entry = {
                            'date': entry_date,
                            'facility_name': facility_name,
                            'enforcement_action': enforcement_action,
                            'pdf_url': pdf_url,
                            'scraped_at': datetime.now()
                        }
                        
                        entries.append(entry)
                        
                except Exception as e:
                    logger.warning(f"Error parsing row: {str(e)}")
                    continue
        
        return entries
    
    def get_last_check_date(self):
        """Get the date of the last successful check."""
        try:
            if os.path.exists(self.last_check_file):
                with open(self.last_check_file, 'r') as f:
                    date_str = f.read().strip()
                    return datetime.fromisoformat(date_str)
        except Exception as e:
            logger.warning(f"Error reading last check date: {str(e)}")
        
        # Default to September 15, 2025 as the cutoff date
        cutoff_date = datetime(2025, 9, 15)
        return cutoff_date
    
    def save_last_check_date(self, date):
        """Save the current check date."""
        try:
            with open(self.last_check_file, 'w') as f:
                f.write(date.isoformat())
        except Exception as e:
            logger.warning(f"Error saving last check date: {str(e)}")
    
    def get_new_entries(self):
        """Get new entries since the last check."""
        try:
            # Get page content
            html_content = self.get_page_content()
            
            # Parse all entries
            all_entries = self.parse_entries(html_content)
            
            # Get last check date
            last_check = self.get_last_check_date()
            
            # Filter for new entries from September 15, 2025 forward
            cutoff_date = datetime(2025, 9, 15)
            new_entries = [
                entry for entry in all_entries 
                if entry['date'] >= cutoff_date and entry['date'] > last_check
            ]
            
            # Update last check date
            self.save_last_check_date(datetime.now())
            
            logger.info(f"Found {len(new_entries)} new entries since {last_check} (from 9/15/2025 forward)")
            return new_entries
            
        except Exception as e:
            logger.error(f"Error getting new entries: {str(e)}")
            raise
    
    def get_entries_from_date(self, start_date=None):
        """Get all entries from a specific date forward."""
        try:
            if start_date is None:
                start_date = datetime(2025, 9, 15)  # Default to September 15, 2025
            
            # Get page content
            html_content = self.get_page_content()
            
            # Parse all entries
            all_entries = self.parse_entries(html_content)
            
            # Filter entries from the specified date forward
            filtered_entries = [
                entry for entry in all_entries 
                if entry['date'] >= start_date
            ]
            
            logger.info(f"Found {len(filtered_entries)} entries from {start_date.strftime('%m/%d/%Y')} forward")
            return filtered_entries
            
        except Exception as e:
            logger.error(f"Error getting entries from date: {str(e)}")
            raise
    
    def download_pdf(self, pdf_url):
        """Download PDF content from URL."""
        try:
            if not pdf_url:
                raise ValueError("No PDF URL provided")
            
            logger.info(f"Downloading PDF from: {pdf_url}")
            response = self.session.get(pdf_url, timeout=60)
            response.raise_for_status()
            
            # Check if it's actually a PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type:
                logger.warning(f"URL may not be a PDF. Content-Type: {content_type}")
            
            return response.content
            
        except requests.RequestException as e:
            logger.error(f"Error downloading PDF from {pdf_url}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error downloading PDF: {str(e)}")
            raise
    
    def get_all_entries(self):
        """Get all entries from the website (for testing purposes)."""
        try:
            html_content = self.get_page_content()
            return self.parse_entries(html_content)
        except Exception as e:
            logger.error(f"Error getting all entries: {str(e)}")
            raise
