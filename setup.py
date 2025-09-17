#!/usr/bin/env python3
"""
Setup script for NJ Health Facility Enforcement Actions Monitor.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def install_dependencies():
    """Install required Python packages."""
    try:
        logger.info("Installing Python dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        logger.info("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing dependencies: {e}")
        return False

def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path("env_example.txt")
    
    if not env_file.exists() and env_example.exists():
        try:
            with open(env_example, 'r') as f:
                content = f.read()
            
            with open(env_file, 'w') as f:
                f.write(content)
            
            logger.info("Created .env file from template. Please update with your actual values.")
            return True
        except Exception as e:
            logger.error(f"Error creating .env file: {e}")
            return False
    elif env_file.exists():
        logger.info(".env file already exists")
        return True
    else:
        logger.warning("No env_example.txt found")
        return False

def check_tesseract():
    """Check if Tesseract OCR is installed."""
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info("Tesseract OCR is installed")
            return True
        else:
            logger.warning("Tesseract OCR not found. OCR functionality will not work.")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        logger.warning("Tesseract OCR not found. OCR functionality will not work.")
        return False

def check_chrome_driver():
    """Check if ChromeDriver is available."""
    try:
        result = subprocess.run(['chromedriver', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info("ChromeDriver is installed")
            return True
        else:
            logger.warning("ChromeDriver not found. Web scraping may not work properly.")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        logger.warning("ChromeDriver not found. Web scraping may not work properly.")
        return False

def create_directories():
    """Create necessary directories."""
    directories = ['logs', 'data', 'temp']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        logger.info(f"Created directory: {directory}")

def setup_gmail_credentials():
    """Provide instructions for Gmail API setup."""
    print("\n" + "="*60)
    print("GMAIL API SETUP REQUIRED")
    print("="*60)
    print("To use Gmail API, you need to:")
    print("1. Go to Google Cloud Console (https://console.cloud.google.com/)")
    print("2. Create a new project or select existing one")
    print("3. Enable Gmail API")
    print("4. Create credentials (OAuth 2.0 Client ID)")
    print("5. Download the credentials JSON file")
    print("6. Rename it to 'credentials.json' and place it in this directory")
    print("7. Update the GMAIL_CREDENTIALS_FILE in your .env file")
    print("="*60)

def setup_supabase():
    """Provide instructions for Supabase setup."""
    print("\n" + "="*60)
    print("SUPABASE SETUP REQUIRED")
    print("="*60)
    print("To use Supabase, you need to:")
    print("1. Go to Supabase (https://supabase.com/)")
    print("2. Create a new project")
    print("3. Go to Settings > API")
    print("4. Copy your Project URL and anon key")
    print("5. Update SUPABASE_URL and SUPABASE_KEY in your .env file")
    print("6. Run the SQL schema from supabase_schema.sql in your Supabase SQL editor")
    print("="*60)

def main():
    """Main setup function."""
    print("Setting up NJ Health Facility Enforcement Actions Monitor...")
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    success = True
    
    # Install dependencies
    if not install_dependencies():
        success = False
    
    # Create .env file
    if not create_env_file():
        success = False
    
    # Create directories
    create_directories()
    
    # Check external dependencies
    check_tesseract()
    check_chrome_driver()
    
    # Provide setup instructions
    setup_gmail_credentials()
    setup_supabase()
    
    print("\n" + "="*60)
    if success:
        print("Setup completed successfully!")
        print("Next steps:")
        print("1. Update your .env file with actual API keys and credentials")
        print("2. Set up Gmail API credentials")
        print("3. Set up Supabase database")
        print("4. Run: python main.py --once (to test)")
        print("5. Run: python main.py (to start the scheduler)")
    else:
        print("Setup completed with some issues. Please check the logs above.")
    print("="*60)

if __name__ == "__main__":
    main()
