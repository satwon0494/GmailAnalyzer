# Gmail Analyzer

A Python tool to analyze Gmail inbox data and generate CSV reports with email sender insights.

## Features

- **Sender Analysis**: Get detailed statistics for each email sender
- **Volume Metrics**: Total emails and monthly averages per sender
- **Date Tracking**: First and last email dates for each sender
- **CSV Export**: Clean, structured data export
- **Time Range Filtering**: Analyze specific date periods

## Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Gmail API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Gmail API
4. Create credentials (OAuth 2.0 Client ID) for desktop application
5. Download the credentials JSON file and save as `credentials.json`

### 3. First Run Authentication
On first run, you'll be redirected to authenticate with Google and grant access to your Gmail.

## Usage

### Basic Usage
```bash
python gmail_analyzer.py --start-date 2023/01/01 --end-date 2023/12/31
```

### Advanced Options
```bash
python gmail_analyzer.py \
  --start-date 2023/01/01 \
  --end-date 2023/12/31 \
  --max-emails 5000 \
  --output my_analysis.csv \
  --credentials my_credentials.json
```

### Parameters
- `--start-date`: Start date (YYYY/MM/DD format, required)
- `--end-date`: End date (YYYY/MM/DD format, required)  
- `--max-emails`: Maximum emails to fetch (default: 1000)
- `--output`: Output CSV filename (default: gmail_analysis.csv)
- `--credentials`: Path to credentials file (default: credentials.json)

## Output CSV Columns

- **sender_email**: Email address of sender
- **sender_name**: Display name of sender
- **total_emails**: Total number of emails received
- **monthly_average**: Average emails per month from this sender
- **first_email_date**: Date of first email received
- **last_email_date**: Date of most recent email
- **time_span_days**: Number of days between first and last email

## Example Output

```csv
sender_email,sender_name,total_emails,monthly_average,first_email_date,last_email_date,time_span_days
notifications@github.com,GitHub,245,20.4,2023-01-05 10:30:00,2023-12-28 16:45:00,357
noreply@linkedin.com,LinkedIn,89,7.4,2023-01-10 08:15:00,2023-12-20 14:20:00,344
```

## Security Notes

- Credentials are stored locally and never transmitted
- Uses OAuth 2.0 for secure authentication
- Only requires read-only access to Gmail
- Token is cached locally for subsequent runs

## Troubleshooting

- Ensure Gmail API is enabled in Google Cloud Console
- Check that credentials.json is in the correct directory
- For large inboxes, increase --max-emails parameter
- Date format must be YYYY/MM/DD