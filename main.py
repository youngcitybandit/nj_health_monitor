#!/usr/bin/env python3
"""
NJ Health Facility Enforcement Actions Monitor
Main application that orchestrates the monitoring, parsing, and notification process.
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

from web_scraper import NJHealthScraper
from pdf_parser import PDFParser
from data_processor import DataProcessor
from email_sender import EmailSender
from database_manager import DatabaseManager
from scheduler import TaskScheduler

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nj_health_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class NJHealthMonitor:
    """Main class that orchestrates the monitoring process."""
    
    def __init__(self):
        """Initialize the monitor with all required components."""
        self.scraper = NJHealthScraper()
        self.pdf_parser = PDFParser()
        self.data_processor = DataProcessor()
        self.email_sender = EmailSender()
        self.db_manager = DatabaseManager()
        self.scheduler = TaskScheduler()
        
    def run_daily_check(self):
        """Run the daily monitoring check."""
        try:
            logger.info("Starting daily NJ Health Facility monitoring check...")
            
            # Step 1: Scrape the website for new entries
            logger.info("Scraping website for new enforcement actions...")
            new_entries = self.scraper.get_new_entries()
            
            if not new_entries:
                logger.info("No new entries found today.")
                return
            
            logger.info(f"Found {len(new_entries)} new entries")
            
            # Step 2: Process each new entry
            processed_entries = []
            for entry in new_entries:
                try:
                    logger.info(f"Processing entry: {entry['facility_name']}")
                    
                    # Download and parse PDF
                    pdf_content = self.scraper.download_pdf(entry['pdf_url'])
                    parsed_data = self.pdf_parser.parse_pdf(pdf_content)
                    
                    # Process and structure the data
                    structured_data = self.data_processor.process_entry(entry, parsed_data)
                    
                    # Store in database
                    self.db_manager.store_entry(structured_data)
                    
                    processed_entries.append(structured_data)
                    logger.info(f"Successfully processed: {entry['facility_name']}")
                    
                except Exception as e:
                    logger.error(f"Error processing entry {entry['facility_name']}: {str(e)}")
                    continue
            
            # Step 3: Generate and send email if there are new entries
            if processed_entries:
                logger.info("Generating and sending email notifications...")
                
                # Load custom prompt if available
                custom_prompt = self._load_custom_prompt()
                
                # Send individual emails to each facility
                for entry in processed_entries:
                    try:
                        success = self.email_sender.send_email_to_facility(entry, custom_prompt)
                        if success:
                            facility_name = entry.get('structured_data', {}).get('facility_name', 'Unknown')
                            logger.info(f"Email sent successfully to {facility_name}")
                        else:
                            logger.warning(f"Failed to send email for {facility_name}")
                    except Exception as e:
                        logger.error(f"Error sending email: {str(e)}")
                
                logger.info(f"Email notifications completed for {len(processed_entries)} facilities")
            
            logger.info("Daily check completed successfully")
            
        except Exception as e:
            logger.error(f"Error in daily check: {str(e)}")
            raise
    
    def _load_custom_prompt(self):
        """Load custom prompt from file if available."""
        try:
            prompt_file = "custom_prompt.txt"
            if os.path.exists(prompt_file):
                with open(prompt_file, 'r') as f:
                    custom_prompt = f.read().strip()
                    logger.info("Loaded custom email prompt from file")
                    return custom_prompt
        except Exception as e:
            logger.warning(f"Could not load custom prompt: {str(e)}")
        
        return None
    
    def run_once(self):
        """Run the monitoring process once (for testing)."""
        self.run_daily_check()
    
    def start_scheduler(self):
        """Start the twice-daily scheduler."""
        logger.info("Starting twice-daily scheduler...")
        # Schedule for 9 AM EST and 2 PM EST
        self.scheduler.schedule_multiple_daily_tasks(self.run_daily_check, ["09:00", "14:00"])
        self.scheduler.run()

def main():
    """Main entry point."""
    monitor = NJHealthMonitor()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # Run once for testing
        monitor.run_once()
    else:
        # Start the scheduler
        monitor.start_scheduler()

if __name__ == "__main__":
    main()
