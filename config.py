"""
Configuration settings for NJ Health Facility Enforcement Actions Monitor.
"""

import os
from datetime import time

class Config:
    """Configuration class with all system settings."""
    
    # Website Configuration
    TARGET_URL = "https://www.nj.gov/health/healthfacilities/surveys-insp/enforcement_actions.shtml"
    CHECK_INTERVAL_HOURS = 12  # Check twice daily
    DAILY_CHECK_TIMES = [time(9, 0), time(14, 0)]  # 9:00 AM EST and 2:00 PM EST
    
    # Monitoring Configuration
    MONITORING_START_DATE = "2025-09-15"  # Only process violations from this date forward
    
    # Web Scraping Configuration
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds
    
    # PDF Processing Configuration
    PDF_DOWNLOAD_TIMEOUT = 60
    OCR_RESOLUTION_MULTIPLIER = 2.0  # Increase resolution for better OCR
    MAX_PDF_SIZE_MB = 50  # Maximum PDF size to process
    
    # Data Processing Configuration
    MIN_TEXT_LENGTH_FOR_OCR = 50  # Minimum text length before trying OCR
    MAX_VIOLATIONS_TO_EXTRACT = 10  # Maximum number of violations to extract
    VIOLATION_SUMMARY_MAX_LENGTH = 500  # Maximum length for violation summary
    
    # Email Configuration
    EMAIL_TEMPLATE_MAX_TOKENS = 2000
    EMAIL_TEMPERATURE = 0.7
    EMAIL_MODEL = "gpt-4"
    
    # Database Configuration
    BATCH_SIZE = 10  # Number of entries to process in batch
    MAX_DB_RETRIES = 3
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = 'nj_health_monitor.log'
    MAX_LOG_SIZE_MB = 10
    LOG_BACKUP_COUNT = 5
    
    # File Paths
    LAST_CHECK_FILE = 'last_check.txt'
    TEMP_DIR = 'temp'
    LOGS_DIR = 'logs'
    DATA_DIR = 'data'
    
    # Severity Thresholds
    HIGH_SEVERITY_KEYWORDS = ['revocation', 'suspension', 'cease']
    MEDIUM_SEVERITY_KEYWORDS = ['curtailment', 'penalties']
    HIGH_PENALTY_THRESHOLD = 10000
    MEDIUM_PENALTY_THRESHOLD = 1000
    
    # Priority Scoring
    PRIORITY_WEIGHTS = {
        'action_type': {
            'revocation': 40,
            'suspension': 40,
            'cease': 30,
            'curtailment': 20,
            'penalties': 15
        },
        'penalty_amount': {
            'high': 30,    # >= 50000
            'medium': 20,  # >= 10000
            'low': 10      # >= 1000
        },
        'violations': {
            'many': 15,    # >= 5
            'some': 10,    # >= 3
            'few': 5       # >= 1
        },
        'recency': {
            'very_recent': 10,  # <= 1 day
            'recent': 5         # <= 7 days
        }
    }
    
    # Email Templates
    EMAIL_SUBJECT_TEMPLATES = {
        'single': "NJ Health Facility Enforcement Action - {facility_name}",
        'multiple': "NJ Health Facility Enforcement Actions - {count} New Entries",
        'urgent': "URGENT: NJ Health Facility Enforcement Actions - {count} High Priority"
    }
    
    # Validation Rules
    REQUIRED_FIELDS = ['facility_name', 'enforcement_action_type', 'enforcement_date']
    OPTIONAL_FIELDS = [
        'facility_address', 'facility_license_number', 'penalty_amount',
        'violation_summary', 'key_violations', 'effective_date'
    ]
    
    # Rate Limiting
    API_RATE_LIMIT = {
        'openai': 60,  # requests per minute
        'gmail': 100,  # requests per minute
        'supabase': 1000  # requests per minute
    }
    
    # Error Handling
    MAX_CONSECUTIVE_ERRORS = 5
    ERROR_BACKOFF_MULTIPLIER = 2
    MAX_BACKOFF_SECONDS = 300
    
    @classmethod
    def get_database_config(cls):
        """Get database configuration."""
        return {
            'url': os.getenv('SUPABASE_URL'),
            'key': os.getenv('SUPABASE_KEY'),
            'timeout': 30
        }
    
    @classmethod
    def get_email_config(cls):
        """Get email configuration."""
        return {
            'sender': os.getenv('SENDER_EMAIL'),
            'recipient': os.getenv('RECIPIENT_EMAIL'),
            'credentials_file': os.getenv('GMAIL_CREDENTIALS_FILE', 'credentials.json'),
            'token_file': os.getenv('GMAIL_TOKEN_FILE', 'token.json')
        }
    
    @classmethod
    def get_openai_config(cls):
        """Get OpenAI configuration."""
        return {
            'api_key': os.getenv('OPENAI_API_KEY'),
            'model': cls.EMAIL_MODEL,
            'max_tokens': cls.EMAIL_TEMPLATE_MAX_TOKENS,
            'temperature': cls.EMAIL_TEMPERATURE
        }
    
    @classmethod
    def get_selenium_config(cls):
        """Get Selenium configuration."""
        return {
            'driver_path': os.getenv('CHROME_DRIVER_PATH', '/usr/local/bin/chromedriver'),
            'headless': True,
            'window_size': (1920, 1080),
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    @classmethod
    def validate_config(cls):
        """Validate that all required configuration is present."""
        required_env_vars = [
            'OPENAI_API_KEY',
            'SUPABASE_URL',
            'SUPABASE_KEY',
            'SENDER_EMAIL',
            'RECIPIENT_EMAIL'
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
