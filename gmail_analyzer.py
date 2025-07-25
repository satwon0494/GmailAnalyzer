#!/usr/bin/env python3
"""
Gmail Analyzer - Extract insights from Gmail inbox data
Generates CSV reports with sender statistics, volume analysis, and date ranges
"""

import os
import pickle
import csv
import time
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional
import argparse

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import pandas as pd
from tqdm import tqdm

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class GmailAnalyzer:
    def __init__(self, credentials_path: str = 'credentials.json'):
        self.credentials_path = credentials_path
        self.service = None
        self.emails_data = []
        
    def authenticate(self) -> None:
        """Authenticate with Gmail API"""
        creds = None
        token_path = 'token.pickle'
        
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
                
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
                
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
                
        self.service = build('gmail', 'v1', credentials=creds)
        
    def fetch_emails(self, start_date: str, end_date: str, max_results: Optional[int] = 10000) -> List[Dict]:
        """Fetch emails from Gmail within date range with pagination support"""
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
            
        # Fix date range: Gmail 'before' is exclusive, so add 1 day to end_date
        from datetime import datetime, timedelta
        try:
            end_dt = datetime.strptime(end_date, "%Y/%m/%d")
            adjusted_end_dt = end_dt + timedelta(days=1)
            adjusted_end_date = adjusted_end_dt.strftime("%Y/%m/%d")
        except ValueError:
            raise ValueError(f"Invalid date format. Use YYYY/MM/DD format. Got: {end_date}")
            
        # Create Gmail query
        query = f'after:{start_date} before:{adjusted_end_date}'
        
        print(f"Fetching emails from {start_date} to {end_date} (inclusive)...")
        print(f"Gmail query: {query}")
        
        # Fetch all messages with pagination
        all_messages = []
        page_token = None
        
        while True:
            try:
                if page_token:
                    results = self.service.users().messages().list(
                        userId='me', q=query, maxResults=500, pageToken=page_token).execute()
                else:
                    results = self.service.users().messages().list(
                        userId='me', q=query, maxResults=500).execute()
                
                messages = results.get('messages', [])
                all_messages.extend(messages)
                
                page_token = results.get('nextPageToken')
                
                print(f"Fetched {len(messages)} messages (total: {len(all_messages)})")
                
                # Stop if we've reached max_results or no more pages
                if not page_token or (max_results and len(all_messages) >= max_results):
                    break
                    
            except Exception as e:
                print(f"Error fetching messages: {e}")
                break
        
        # Limit to max_results if specified
        if max_results and len(all_messages) > max_results:
            all_messages = all_messages[:max_results]
            print(f"Limited to {max_results} most recent messages")
        
        if not all_messages:
            print("No messages found in the specified date range.")
            return []
            
        print(f"Processing {len(all_messages)} messages for detailed analysis...")
        
        emails = []
        failed_messages = []
        
        for message in tqdm(all_messages, desc="Processing emails"):
            success = False
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    msg = self.service.users().messages().get(
                        userId='me', id=message['id'], format='metadata',
                        metadataHeaders=['From', 'Date', 'Subject']).execute()
                    
                    headers = {h['name']: h['value'] for h in msg['payload']['headers']}
                    
                    email_data = {
                        'message_id': message['id'],
                        'sender': self._extract_email(headers.get('From', '')),
                        'sender_name': self._extract_name(headers.get('From', '')),
                        'date': headers.get('Date', ''),
                        'subject': headers.get('Subject', ''),
                        'timestamp': self._parse_date(headers.get('Date', ''))
                    }
                    
                    emails.append(email_data)
                    success = True
                    break
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        # Wait before retry (exponential backoff)
                        wait_time = (2 ** attempt)
                        time.sleep(wait_time)
                        continue
                    else:
                        # Final attempt failed
                        failed_messages.append(message['id'])
                        tqdm.write(f"Failed to process message {message['id']} after {max_retries} attempts: {e}")
                        break
        
        if failed_messages:
            print(f"\nWarning: Failed to process {len(failed_messages)} messages due to network issues.")
            print(f"Successfully processed {len(emails)} out of {len(all_messages)} messages.")
                
        self.emails_data = emails
        print(f"Final count: {len(emails)} emails processed successfully.")
        return emails
        
    def _extract_email(self, from_field: str) -> str:
        """Extract email address from From field"""
        if '<' in from_field and '>' in from_field:
            return from_field.split('<')[1].split('>')[0].strip()
        return from_field.strip()
        
    def _extract_name(self, from_field: str) -> str:
        """Extract sender name from From field"""
        if '<' in from_field:
            return from_field.split('<')[0].strip().strip('"')
        return from_field.split('@')[0] if '@' in from_field else from_field
        
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse email date string to datetime object (timezone-naive for consistency)"""
        if not date_str:
            return None
            
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            # Convert to timezone-naive UTC for consistent comparisons
            if dt.tzinfo is not None:
                dt = dt.utctimetuple()
                dt = datetime(*dt[:6])  # Convert to naive datetime
            return dt
        except Exception:
            return None
            
    def analyze_senders(self) -> List[Dict]:
        """Analyze email senders and generate statistics"""
        if not self.emails_data:
            return []
            
        sender_stats = defaultdict(lambda: {
            'sender_email': '',
            'sender_name': '',
            'total_emails': 0,
            'first_email_date': None,
            'last_email_date': None,
            'dates': []
        })
        
        # Collect data for each sender
        for email in self.emails_data:
            sender = email['sender']
            timestamp = email['timestamp']
            
            if not sender or not timestamp:
                continue
                
            # Handle string timestamps from cached data
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    # Convert to timezone-naive for consistency
                    if timestamp.tzinfo is not None:
                        timestamp = timestamp.replace(tzinfo=None)
                except ValueError:
                    try:
                        timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        continue
                        
            stats = sender_stats[sender]
            stats['sender_email'] = sender
            stats['sender_name'] = email['sender_name']
            stats['total_emails'] += 1
            stats['dates'].append(timestamp)
            
            if not stats['first_email_date'] or timestamp < stats['first_email_date']:
                stats['first_email_date'] = timestamp
                
            if not stats['last_email_date'] or timestamp > stats['last_email_date']:
                stats['last_email_date'] = timestamp
                
        # Calculate monthly averages and format results
        results = []
        for sender, stats in sender_stats.items():
            if stats['first_email_date'] and stats['last_email_date']:
                # Calculate time span in months
                time_span = (stats['last_email_date'] - stats['first_email_date']).days
                months = max(1, time_span / 30.44)  # Average days per month
                monthly_average = stats['total_emails'] / months
                
                results.append({
                    'sender_email': stats['sender_email'],
                    'sender_name': stats['sender_name'],
                    'total_emails': stats['total_emails'],
                    'monthly_average': round(monthly_average, 2),
                    'first_email_date': stats['first_email_date'].strftime('%Y-%m-%d %H:%M:%S'),
                    'last_email_date': stats['last_email_date'].strftime('%Y-%m-%d %H:%M:%S'),
                    'time_span_days': time_span
                })
                
        # Sort by total emails descending
        results.sort(key=lambda x: x['total_emails'], reverse=True)
        return results
        
    def export_to_csv(self, analysis_results: List[Dict], output_file: str = 'gmail_analysis.csv') -> None:
        """Export analysis results to CSV file"""
        if not analysis_results:
            print("No data to export.")
            return
            
        df = pd.DataFrame(analysis_results)
        df.to_csv(output_file, index=False)
        print(f"Analysis exported to {output_file}")
        print(f"Total senders analyzed: {len(analysis_results)}")
        print(f"Total emails processed: {sum(r['total_emails'] for r in analysis_results)}")

def main():
    parser = argparse.ArgumentParser(description='Analyze Gmail inbox and generate CSV report')
    parser.add_argument('--credentials', default='credentials.json', 
                       help='Path to Google API credentials JSON file')
    parser.add_argument('--start-date', required=True,
                       help='Start date for analysis (YYYY/MM/DD format)')
    parser.add_argument('--end-date', required=True,
                       help='End date for analysis (YYYY/MM/DD format)')
    parser.add_argument('--max-emails', type=int, default=10000,
                       help='Maximum number of emails to fetch (default: 10000, use 0 for unlimited)')
    parser.add_argument('--output', default='gmail_analysis.csv',
                       help='Output CSV file name (default: gmail_analysis.csv)')
    
    args = parser.parse_args()
    
    try:
        analyzer = GmailAnalyzer(args.credentials)
        analyzer.authenticate()
        
        # Handle unlimited emails case
        max_emails = None if args.max_emails == 0 else args.max_emails
        emails = analyzer.fetch_emails(args.start_date, args.end_date, max_emails)
        
        if emails:
            analysis = analyzer.analyze_senders()
            analyzer.export_to_csv(analysis, args.output)
        else:
            print("No emails found in the specified date range.")
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure to download your Gmail API credentials and save as 'credentials.json'")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()