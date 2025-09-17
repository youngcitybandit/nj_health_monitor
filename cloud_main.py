#!/usr/bin/env python3
"""
Cloud Run compatible main file for NJ Health Facility Monitor.
Handles HTTP requests from Cloud Scheduler.
"""

import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your existing components
from web_scraper import NJHealthScraper
from pdf_parser import PDFParser
from data_processor import DataProcessor
from email_sender import EmailSender
from database_manager import DatabaseManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

class CloudNJHealthMonitor:
    """Cloud Run compatible NJ Health Monitor."""
    
    def __init__(self):
        """Initialize the monitor components."""
        self.scraper = NJHealthScraper()
        self.pdf_parser = PDFParser()
        self.data_processor = DataProcessor()
        self.email_sender = EmailSender()
        
        # Initialize database if configured
        try:
            self.database_manager = DatabaseManager()
        except Exception as e:
            logger.warning(f"Database not configured: {str(e)}")
            self.database_manager = None
    
    def run_check(self):
        """Run a single check for new violations."""
        try:
            logger.info("Starting enforcement actions check...")
            
            # Step 1: Get new entries from the website
            logger.info("Checking for new enforcement actions...")
            new_entries = self.scraper.get_new_entries()
            
            if not new_entries:
                logger.info("No new enforcement actions found")
                return {"status": "success", "new_entries": 0, "emails_sent": 0}
            
            logger.info(f"Found {len(new_entries)} new enforcement actions")
            
            # Step 2: Process each entry
            processed_entries = []
            for entry in new_entries:
                try:
                    logger.info(f"Processing: {entry['facility_name']}")
                    
                    # Parse PDF content
                    # Download and parse PDF
                    import requests
                    pdf_response = requests.get(entry['pdf_url'])
                    pdf_data = self.pdf_parser.parse_pdf(pdf_response.content)
                    
                    # Process the data
                    processed_entry = self.data_processor.process_entry(entry, pdf_data)
                    
                    if processed_entry:
                        processed_entries.append(processed_entry)
                        
                        # Store in database if available
                        if self.database_manager:
                            try:
                                self.database_manager.store_entry(processed_entry)
                            except Exception as e:
                                logger.warning(f"Database storage failed: {str(e)}")
                    
                except Exception as e:
                    logger.error(f"Error processing {entry.get('facility_name', 'unknown')}: {str(e)}")
                    continue
            
            # Step 3: Generate and send emails
            emails_sent = 0
            if processed_entries:
                logger.info("Generating and sending email notifications...")
                
                # Load custom prompt if available
                custom_prompt = self._load_custom_prompt()
                
                # Send individual emails to each facility
                for entry in processed_entries:
                    try:
                        success = self.email_sender.send_email_to_facility(entry, custom_prompt)
                        if success:
                            emails_sent += 1
                            facility_name = entry.get('structured_data', {}).get('facility_name', 'Unknown')
                            logger.info(f"Email sent successfully to {facility_name}")
                        else:
                            logger.warning(f"Failed to send email for {facility_name}")
                    except Exception as e:
                        logger.error(f"Error sending email: {str(e)}")
            
            logger.info(f"Check completed: {len(processed_entries)} processed, {emails_sent} emails sent")
            
            return {
                "status": "success",
                "new_entries": len(new_entries),
                "processed_entries": len(processed_entries),
                "emails_sent": emails_sent,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Check failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
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

# Initialize the monitor
monitor = CloudNJHealthMonitor()

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "NJ Health Facility Monitor",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/check', methods=['POST'])
def run_check():
    """Endpoint to trigger a check (called by Cloud Scheduler)."""
    try:
        # Verify request is from Cloud Scheduler (optional security)
        # You can add authentication here if needed
        
        logger.info("Received check request from Cloud Scheduler")
        result = monitor.run_check()
        
        return jsonify(result), 200 if result["status"] == "success" else 500
        
    except Exception as e:
        logger.error(f"Check endpoint failed: {str(e)}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/test', methods=['GET'])
def test_check():
    """Test endpoint for manual testing."""
    logger.info("Received manual test request")
    result = monitor.run_check()
    return jsonify(result), 200 if result["status"] == "success" else 500

if __name__ == '__main__':
    # Get port from environment (Cloud Run sets this)
    port = int(os.environ.get('PORT', 8080))
    
    logger.info(f"Starting NJ Health Monitor on port {port}")
    logger.info("Endpoints available:")
    logger.info("  GET  /     - Health check")
    logger.info("  POST /check - Run check (for Cloud Scheduler)")
    logger.info("  GET  /test  - Manual test")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=False)
