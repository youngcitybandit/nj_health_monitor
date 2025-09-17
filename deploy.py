#!/usr/bin/env python3
"""
Deployment script for NJ Health Facility Enforcement Actions Monitor.
Handles installation, configuration, and startup.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

def setup_logging():
    """Setup logging for deployment."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible."""
    logger = logging.getLogger(__name__)
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required")
        return False
    logger.info(f"Python version {sys.version} is compatible")
    return True

def install_dependencies():
    """Install required dependencies."""
    logger = logging.getLogger(__name__)
    try:
        logger.info("Installing dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        logger.info("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False

def check_system_dependencies():
    """Check for required system dependencies."""
    logger = logging.getLogger(__name__)
    
    # Check Tesseract
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info("✓ Tesseract OCR found")
        else:
            logger.warning("⚠ Tesseract OCR not found - OCR functionality will not work")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        logger.warning("⚠ Tesseract OCR not found - OCR functionality will not work")
    
    # Check ChromeDriver
    try:
        result = subprocess.run(['chromedriver', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info("✓ ChromeDriver found")
        else:
            logger.warning("⚠ ChromeDriver not found - web scraping may not work")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        logger.warning("⚠ ChromeDriver not found - web scraping may not work")

def create_directories():
    """Create necessary directories."""
    logger = logging.getLogger(__name__)
    directories = ['logs', 'data', 'temp']
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        logger.info(f"Created directory: {directory}")

def check_environment():
    """Check environment configuration."""
    logger = logging.getLogger(__name__)
    
    # Check if .env file exists
    if not Path('.env').exists():
        logger.error("❌ .env file not found. Please copy env_example.txt to .env and configure it.")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check required environment variables
    required_vars = [
        'OPENAI_API_KEY',
        'SUPABASE_URL', 
        'SUPABASE_KEY',
        'SENDER_EMAIL',
        'RECIPIENT_EMAIL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    logger.info("✓ Environment configuration is valid")
    return True

def run_tests():
    """Run system tests."""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Running system tests...")
        result = subprocess.run([sys.executable, "test_system.py"], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            logger.info("✓ All tests passed")
            return True
        else:
            logger.error(f"❌ Tests failed:\n{result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error("❌ Tests timed out")
        return False
    except Exception as e:
        logger.error(f"❌ Error running tests: {e}")
        return False

def start_monitor():
    """Start the monitoring system."""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting NJ Health Facility Monitor...")
        subprocess.run([sys.executable, "main.py"])
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
    except Exception as e:
        logger.error(f"Error starting monitor: {e}")

def main():
    """Main deployment function."""
    logger = setup_logging()
    
    logger.info("🚀 Deploying NJ Health Facility Enforcement Actions Monitor")
    logger.info("=" * 60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        logger.error("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Check system dependencies
    check_system_dependencies()
    
    # Create directories
    create_directories()
    
    # Check environment
    if not check_environment():
        logger.error("❌ Environment configuration is invalid")
        sys.exit(1)
    
    # Run tests
    if not run_tests():
        logger.error("❌ System tests failed")
        sys.exit(1)
    
    logger.info("✅ Deployment completed successfully!")
    logger.info("=" * 60)
    
    # Ask user if they want to start the monitor
    try:
        response = input("Do you want to start the monitor now? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            start_monitor()
        else:
            logger.info("You can start the monitor later with: python main.py")
    except KeyboardInterrupt:
        logger.info("\nDeployment completed. You can start the monitor later with: python main.py")

if __name__ == "__main__":
    main()
