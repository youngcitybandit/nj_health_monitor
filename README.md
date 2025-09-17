# NJ Health Facility Enforcement Actions Monitor

An automated monitoring system that tracks New Jersey health facility enforcement actions, extracts data from PDFs using OCR when needed, and sends email notifications using ChatGPT-generated content.

## Features

- **Daily Website Monitoring**: Automatically checks the NJ Department of Health website for new enforcement actions
- **PDF Processing**: Downloads and parses PDF documents, with OCR support for scanned documents
- **Intelligent Data Extraction**: Extracts key information like facility names, violation details, penalty amounts, and more
- **AI-Powered Email Generation**: Uses ChatGPT to generate professional email notifications
- **Gmail Integration**: Sends emails directly from your Gmail account
- **Database Storage**: Stores all data in Supabase for tracking and analysis
- **Scheduling**: Runs automatically on a daily schedule
- **Error Handling**: Comprehensive logging and error recovery

## Prerequisites

Before setting up the monitor, ensure you have:

1. **Python 3.8+** installed
2. **Tesseract OCR** installed (for PDF text extraction)
3. **ChromeDriver** installed (for web scraping)
4. **OpenAI API key** (for ChatGPT integration)
5. **Supabase account** (for database storage)
6. **Gmail account** with API access enabled

## Installation

1. **Clone or download** this repository to your local machine

2. **Run the setup script**:
   ```bash
   python setup.py
   ```

3. **Install system dependencies**:

   **On macOS (using Homebrew)**:
   ```bash
   brew install tesseract
   brew install chromedriver
   ```

   **On Ubuntu/Debian**:
   ```bash
   sudo apt-get install tesseract-ocr
   sudo apt-get install chromium-chromedriver
   ```

   **On Windows**:
   - Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
   - Download ChromeDriver from: https://chromedriver.chromium.org/

4. **Configure your environment**:
   - Copy `env_example.txt` to `.env`
   - Update the `.env` file with your actual API keys and credentials

## Configuration

### Environment Variables

Update your `.env` file with the following:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here

# Gmail API Configuration
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.json

# Email Configuration
SENDER_EMAIL=your_email@gmail.com
RECIPIENT_EMAIL=recipient@example.com

# Selenium Configuration
CHROME_DRIVER_PATH=/usr/local/bin/chromedriver
```

### Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API
4. Create OAuth 2.0 credentials
5. Download the credentials JSON file
6. Rename it to `credentials.json` and place it in the project directory

### Supabase Setup

1. Go to [Supabase](https://supabase.com/)
2. Create a new project
3. Go to Settings > API to get your URL and key
4. Run the SQL schema from `supabase_schema.sql` in your Supabase SQL editor

## Usage

### Test Run

To test the system once:

```bash
python main.py --once
```

### Start Daily Monitoring

To start the daily scheduler:

```bash
python main.py
```

The system will:
1. Check for new enforcement actions daily at 9:00 AM
2. Download and parse any new PDFs
3. Generate and send email notifications
4. Store all data in Supabase

### Custom Scheduling

You can modify the schedule in `main.py` or use the scheduler directly:

```python
from scheduler import TaskScheduler

scheduler = TaskScheduler()
scheduler.schedule_daily_task(your_function, "14:30")  # 2:30 PM
scheduler.schedule_hourly_task(your_function)
scheduler.run()
```

## Project Structure

```
nj_health_monitor/
├── main.py                 # Main application entry point
├── web_scraper.py          # Website scraping functionality
├── pdf_parser.py           # PDF parsing and OCR
├── data_processor.py       # Data processing and structuring
├── email_sender.py         # Email generation and sending
├── database_manager.py     # Supabase database operations
├── scheduler.py            # Task scheduling
├── setup.py               # Setup and installation script
├── requirements.txt       # Python dependencies
├── supabase_schema.sql    # Database schema
├── env_example.txt        # Environment variables template
└── README.md              # This file
```

## Data Flow

1. **Website Monitoring**: Daily check of NJ health facility website
2. **PDF Download**: Download new enforcement action PDFs
3. **Text Extraction**: Extract text using PDF libraries or OCR
4. **Data Processing**: Parse and structure the extracted information
5. **Database Storage**: Store processed data in Supabase
6. **Email Generation**: Use ChatGPT to generate professional emails
7. **Email Sending**: Send notifications via Gmail API

## Extracted Data Fields

The system extracts the following information from each enforcement action:

- Facility name and address
- License number
- Enforcement action type
- Penalty amount
- Violation details and summary
- Key violations list
- Effective dates
- Contact information
- Severity assessment
- Priority scoring

## Error Handling

The system includes comprehensive error handling:

- **Logging**: All operations are logged with timestamps
- **Retry Logic**: Failed operations are retried where appropriate
- **Graceful Degradation**: System continues running even if individual entries fail
- **Validation**: Data is validated before storage and email sending

## Monitoring and Logs

- **Application Logs**: Stored in `nj_health_monitor.log`
- **Database Logs**: Stored in Supabase `monitoring_logs` table
- **Email Logs**: Tracked in `email_notifications` table

## Troubleshooting

### Common Issues

1. **Tesseract not found**: Install Tesseract OCR and ensure it's in your PATH
2. **ChromeDriver issues**: Install ChromeDriver and update the path in `.env`
3. **Gmail API errors**: Check your credentials and ensure Gmail API is enabled
4. **Supabase connection**: Verify your URL and key are correct
5. **PDF parsing failures**: Some PDFs may not be parseable; check logs for details

### Debug Mode

Enable debug logging by modifying the logging level in `main.py`:

```python
logging.basicConfig(level=logging.DEBUG, ...)
```

## Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review the logs for error messages
3. Create an issue in the repository
4. Contact the maintainers

## Changelog

### Version 1.0.0
- Initial release
- Basic website monitoring
- PDF parsing with OCR support
- Gmail integration
- Supabase storage
- Daily scheduling
