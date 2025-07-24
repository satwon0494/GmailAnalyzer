#!/usr/bin/env python3
"""
Gmail IMAP Analyzer - Efficient bulk processing via IMAP
More efficient than REST API for large datasets

Performance: ~2000-5000 emails/minute
Pros: Lower latency, bulk header fetching, direct protocol
Cons: More complex OAuth2 setup, less Gmail-specific features
"""

import os
import pickle
import imaplib
import email
import base64
import json
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional
import argparse
import re
from email.utils import parsedate_to_datetime

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import pandas as pd
from tqdm import tqdm

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
IMAP_SERVER = 'imap.gmail.com'
IMAP_PORT = 993

class GmailIMAPAnalyzer:
    def __init__(self, credentials_path: str = 'credentials.json'):
        self.credentials_path = credentials_path
        self.imap = None
        self.emails_data = []
        
    def authenticate_and_connect(self) -> None:
        """Authenticate with OAuth2 and connect to Gmail IMAP"""
        # Get OAuth2 token
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
        
        # Connect to IMAP with OAuth2
        print("🔐 Connecting to Gmail IMAP...")
        self.imap = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        
        # Generate OAuth2 string
        email_address = self._get_email_from_credentials()
        auth_string = self._generate_oauth2_string(email_address, creds.token)
        
        # Authenticate with proper error handling
        try:
            # IMAP authenticate expects a callable that returns bytes
            def auth_callback(challenge):
                return auth_string
            
            self.imap.authenticate('XOAUTH2', auth_callback)
            print("✅ Connected to Gmail IMAP successfully")
            
        except imaplib.IMAP4.error as e:
            error_msg = str(e)
            print(f"❌ IMAP Authentication failed: {error_msg}")
            
            # Provide specific troubleshooting based on error
            if 'Invalid SASL argument' in error_msg or 'BAD' in error_msg:
                print("\n🔧 OAuth2 SASL Error - Try these fixes:")
                print("1. Ensure IMAP is enabled: Gmail → Settings → Forwarding and POP/IMAP → Enable IMAP")
                print("2. Delete token.pickle and re-authenticate")
                print("3. Verify credentials.json is for 'Desktop application' type")
                print("4. Check 2-Step Verification is enabled on your Google account")
                print("5. Try using the Optimized API solution instead: gmail_api_optimized.py")
            elif 'AUTHENTICATE failed' in error_msg:
                print("\n🔧 Authentication Error - Try this:")
                print("1. Regenerate OAuth2 credentials in Google Cloud Console")
                print("2. Ensure Gmail API is enabled")
                print("3. Use 'OAuth 2.0 Client ID' for Desktop application")
            
            # Suggest alternative
            print("\n💡 Recommendation: Use the Optimized API solution for more reliable authentication:")
            print("   python gmail_api_optimized.py --start-date 2014/01/01 --end-date 2025/06/30")
            
            raise RuntimeError(f"IMAP authentication failed. Try the API solution instead.")
        
    def _get_email_from_credentials(self) -> str:
        """Get email address from user input with validation"""
        print("\nFor IMAP authentication, we need your Gmail address.")
        email = input("Enter your Gmail address: ").strip()
        
        # Basic email validation
        if '@' not in email or '.' not in email.split('@')[1]:
            raise ValueError(f"Invalid email format: {email}")
        
        if not email.endswith('@gmail.com'):
            print("⚠️  Warning: This tool is designed for Gmail accounts")
            
        return email
            
    def _generate_oauth2_string(self, email: str, access_token: str) -> bytes:
        """Generate OAuth2 authentication string for IMAP XOAUTH2"""
        # Proper XOAUTH2 format: user=email\x01auth=Bearer token\x01\x01
        auth_string = f'user={email}\x01auth=Bearer {access_token}\x01\x01'
        return base64.b64encode(auth_string.encode('ascii'))
        
    def fetch_emails_imap(self, start_date: str, end_date: str, 
                         max_results: Optional[int] = None) -> List[Dict]:
        """Fetch emails using IMAP with efficient bulk operations"""
        if not self.imap:
            raise RuntimeError("Not connected. Call authenticate_and_connect() first.")
            
        # Select INBOX (or ALL MAIL for complete analysis)
        print("📂 Selecting mailbox...")
        
        # Try to select All Mail first (more comprehensive)
        try:
            self.imap.select('[Gmail]/All Mail')
            print("📧 Using 'All Mail' folder for comprehensive analysis")
        except:
            self.imap.select('INBOX')
            print("📧 Using 'INBOX' folder")
            
        # Convert dates to IMAP format
        start_dt = datetime.strptime(start_date, "%Y/%m/%d")
        end_dt = datetime.strptime(end_date, "%Y/%m/%d")
        
        # IMAP date format: DD-Mon-YYYY
        imap_start = start_dt.strftime("%d-%b-%Y")
        imap_end = end_dt.strftime("%d-%b-%Y")
        
        # Build IMAP search query
        search_criteria = f'SINCE {imap_start} BEFORE {imap_end}'
        print(f"🔍 IMAP search: {search_criteria}")
        
        # Search for messages
        print("🔎 Searching for messages...")
        typ, message_ids = self.imap.search(None, search_criteria)
        
        if typ != 'OK':
            raise RuntimeError(f"IMAP search failed: {typ}")
            
        # Parse message IDs
        message_ids = message_ids[0].split()
        total_messages = len(message_ids)
        
        print(f"📊 Found {total_messages:,} messages in date range")
        
        if max_results and total_messages > max_results:
            # Take most recent messages
            message_ids = message_ids[-max_results:]
            print(f"📝 Limited to {max_results:,} most recent messages")
            
        if not message_ids:
            print("📭 No messages found in the specified date range")
            return []
            
        # Fetch emails in batches for efficiency
        return self._fetch_email_headers_batch(message_ids)
        
    def _fetch_email_headers_batch(self, message_ids: List[bytes]) -> List[Dict]:
        """Fetch email headers in efficient batches"""
        emails = []
        batch_size = 100  # IMAP can handle larger batches than REST API
        
        print(f"📥 Fetching email headers in batches of {batch_size}...")
        
        for i in range(0, len(message_ids), batch_size):
            batch_ids = message_ids[i:i + batch_size]
            
            # Create ID range for batch fetch
            id_range = b','.join(batch_ids).decode()
            
            try:
                # Fetch headers for entire batch
                typ, msg_data = self.imap.fetch(id_range, '(BODY.PEEK[HEADER.FIELDS (FROM DATE SUBJECT MESSAGE-ID)])')
                
                if typ != 'OK':
                    print(f"⚠️  Batch fetch failed: {typ}")
                    continue
                    
                # Process batch results
                batch_emails = self._process_batch_headers(msg_data, batch_ids)
                emails.extend(batch_emails)
                
                # Update progress
                progress = min(i + batch_size, len(message_ids))
                print(f"📈 Processed {progress:,}/{len(message_ids):,} messages ({progress/len(message_ids)*100:.1f}%)")
                
            except Exception as e:
                print(f"⚠️  Batch error: {e}")
                # Fallback to individual processing for this batch
                for msg_id in batch_ids:
                    try:
                        email_data = self._fetch_single_email_imap(msg_id)
                        if email_data:
                            emails.append(email_data)
                    except Exception:
                        continue
                        
        print(f"✅ Successfully processed {len(emails):,} emails")
        self.emails_data = emails
        return emails
        
    def _process_batch_headers(self, msg_data: List, message_ids: List[bytes]) -> List[Dict]:
        """Process batch of email headers"""
        emails = []
        
        # msg_data comes in pairs: (b'ID', b'headers'), (b')', None)
        for i in range(0, len(msg_data), 2):
            try:
                if i + 1 >= len(msg_data):
                    break
                    
                msg_num, headers_data = msg_data[i]
                
                if not headers_data:
                    continue
                    
                # Parse headers
                headers_str = headers_data.decode('utf-8', errors='ignore')
                email_msg = email.message_from_string(headers_str)
                
                # Extract data
                from_field = email_msg.get('From', '')
                date_field = email_msg.get('Date', '')
                subject_field = email_msg.get('Subject', '')
                message_id = email_msg.get('Message-ID', '')
                
                email_data = {
                    'message_id': message_id,
                    'sender': self._extract_email(from_field),
                    'sender_name': self._extract_name(from_field),
                    'date': date_field,
                    'subject': subject_field,
                    'timestamp': self._parse_date(date_field)
                }
                
                emails.append(email_data)
                
            except Exception as e:
                # Skip malformed messages
                continue
                
        return emails
        
    def _fetch_single_email_imap(self, message_id: bytes) -> Optional[Dict]:
        """Fetch single email as fallback"""
        try:
            typ, msg_data = self.imap.fetch(message_id, '(BODY.PEEK[HEADER.FIELDS (FROM DATE SUBJECT MESSAGE-ID)])')
            
            if typ != 'OK' or not msg_data[0][1]:
                return None
                
            headers_str = msg_data[0][1].decode('utf-8', errors='ignore')
            email_msg = email.message_from_string(headers_str)
            
            from_field = email_msg.get('From', '')
            date_field = email_msg.get('Date', '')
            subject_field = email_msg.get('Subject', '')
            msg_id = email_msg.get('Message-ID', '')
            
            return {
                'message_id': msg_id,
                'sender': self._extract_email(from_field),
                'sender_name': self._extract_name(from_field),
                'date': date_field,
                'subject': subject_field,
                'timestamp': self._parse_date(date_field)
            }
            
        except Exception:
            return None
            
    def _extract_email(self, from_field: str) -> str:
        """Extract email address from From field"""
        if not from_field:
            return ''
            
        # Handle various email formats
        email_pattern = r'<([^>]+)>'
        match = re.search(email_pattern, from_field)
        if match:
            return match.group(1).strip()
            
        # Simple email format
        email_pattern = r'\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b'
        match = re.search(email_pattern, from_field)
        if match:
            return match.group(0).strip()
            
        return from_field.strip()
        
    def _extract_name(self, from_field: str) -> str:
        """Extract sender name from From field"""
        if not from_field:
            return ''
            
        if '<' in from_field:
            name = from_field.split('<')[0].strip().strip('"').strip("'")
            return name if name else from_field.split('@')[0] if '@' in from_field else from_field
        elif '@' in from_field:
            return from_field.split('@')[0]
        else:
            return from_field.strip()
            
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse email date to timezone-naive datetime"""
        if not date_str:
            return None
        try:
            dt = parsedate_to_datetime(date_str)
            if dt.tzinfo is not None:
                dt = dt.utctimetuple()
                dt = datetime(*dt[:6])
            return dt
        except Exception:
            return None
            
    def close_connection(self) -> None:
        """Close IMAP connection"""
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
                print("🔒 IMAP connection closed")
            except:
                pass
                
    def analyze_senders(self) -> List[Dict]:
        """Analyze senders - same logic as other methods"""
        if not self.emails_data:
            return []
            
        sender_stats = defaultdict(lambda: {
            'sender_email': '',
            'sender_name': '',
            'total_emails': 0,
            'first_email_date': None,
            'last_email_date': None
        })
        
        for email in self.emails_data:
            sender = email['sender']
            timestamp = email['timestamp']
            
            if not sender or not timestamp:
                continue
                
            stats = sender_stats[sender]
            stats['sender_email'] = sender
            stats['sender_name'] = email['sender_name']
            stats['total_emails'] += 1
            
            if not stats['first_email_date'] or timestamp < stats['first_email_date']:
                stats['first_email_date'] = timestamp
                
            if not stats['last_email_date'] or timestamp > stats['last_email_date']:
                stats['last_email_date'] = timestamp
                
        results = []
        for sender, stats in sender_stats.items():
            if stats['first_email_date'] and stats['last_email_date']:
                time_span = (stats['last_email_date'] - stats['first_email_date']).days
                months = max(1, time_span / 30.44)
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
                
        results.sort(key=lambda x: x['total_emails'], reverse=True)
        return results
        
    def export_to_csv(self, analysis_results: List[Dict], output_file: str) -> None:
        """Export to CSV"""
        if not analysis_results:
            print("No data to export.")
            return
            
        df = pd.DataFrame(analysis_results)
        df.to_csv(output_file, index=False)
        
        print(f"📁 Analysis exported to {output_file}")
        print(f"📊 Senders: {len(analysis_results):,}")
        print(f"📧 Emails: {sum(r['total_emails'] for r in analysis_results):,}")

def main():
    parser = argparse.ArgumentParser(description='Gmail IMAP analyzer (efficient bulk processing)')
    parser.add_argument('--credentials', default='credentials.json')
    parser.add_argument('--start-date', required=True)
    parser.add_argument('--end-date', required=True)
    parser.add_argument('--max-emails', type=int)
    parser.add_argument('--output', default='gmail_imap_analysis.csv')
    
    args = parser.parse_args()
    
    analyzer = None
    try:
        start_time = datetime.now()
        
        analyzer = GmailIMAPAnalyzer(args.credentials)
        analyzer.authenticate_and_connect()
        
        emails = analyzer.fetch_emails_imap(args.start_date, args.end_date, args.max_emails)
        
        if emails:
            analysis = analyzer.analyze_senders()
            analyzer.export_to_csv(analysis, args.output)
            
            # Performance stats
            duration = (datetime.now() - start_time).total_seconds()
            emails_per_minute = len(emails) / (duration / 60) if duration > 0 else 0
            
            print(f"\\n⚡ Performance:")
            print(f"   Time: {duration:.1f}s")
            print(f"   Speed: {emails_per_minute:,.0f} emails/minute")
            print(f"   🌐 IMAP efficiency demonstrated!")
            
    except Exception as e:
        print(f"Error: {e}")
        print("\\n💡 IMAP Setup Notes:")
        print("- Requires same OAuth2 credentials as API")
        print("- May need 'Less secure app access' disabled in Gmail")
        print("- IMAP must be enabled in Gmail settings")
        
    finally:
        if analyzer:
            analyzer.close_connection()

if __name__ == '__main__':
    main()