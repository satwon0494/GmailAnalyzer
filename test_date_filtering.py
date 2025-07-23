#!/usr/bin/env python3
"""
Test cases for debugging Gmail date filtering issues
"""

from datetime import datetime, timedelta
import re

def test_gmail_date_format():
    """Test Gmail API date format requirements"""
    print("=== Gmail Date Format Testing ===")
    
    # Test input formats
    test_dates = [
        "2025/01/01",
        "2025/06/30", 
        "2023/12/31"
    ]
    
    print("\nInput format (YYYY/MM/DD) to Gmail format (YYYY/MM/DD):")
    for date_str in test_dates:
        # Current implementation just passes through
        gmail_format = date_str
        print(f"  {date_str} -> {gmail_format}")
    
    print("\nTesting date conversion to proper Gmail format:")
    for date_str in test_dates:
        # Convert to datetime and back to ensure valid date
        try:
            dt = datetime.strptime(date_str, "%Y/%m/%d")
            gmail_format = dt.strftime("%Y/%m/%d")
            print(f"  {date_str} -> {gmail_format} (valid)")
        except ValueError as e:
            print(f"  {date_str} -> ERROR: {e}")

def test_gmail_query_logic():
    """Test Gmail query behavior with before/after"""
    print("\n=== Gmail Query Logic Testing ===")
    
    start_date = "2025/01/01"
    end_date = "2025/06/30"
    
    # Current implementation
    current_query = f'after:{start_date} before:{end_date}'
    print(f"Current query: {current_query}")
    
    # The issue: Gmail's 'before' is exclusive, 'after' is inclusive
    print("\nGmail query behavior:")
    print(f"  after:{start_date} = emails FROM {start_date} onwards (inclusive)")
    print(f"  before:{end_date} = emails BEFORE {end_date} (exclusive)")
    print(f"  Combined: emails from {start_date} to {end_date} (excluding {end_date})")
    
    # Fix: adjust end date
    end_dt = datetime.strptime(end_date, "%Y/%m/%d")
    adjusted_end = end_dt + timedelta(days=1)
    adjusted_end_str = adjusted_end.strftime("%Y/%m/%d")
    
    fixed_query = f'after:{start_date} before:{adjusted_end_str}'
    print(f"\nFixed query: {fixed_query}")
    print(f"  This will include emails through {end_date}")

def test_edge_cases():
    """Test edge cases for date filtering"""
    print("\n=== Edge Cases Testing ===")
    
    # Same day
    same_day = "2025/06/15"
    query1 = f'after:{same_day} before:{same_day}'
    print(f"Same day query: {query1}")
    print("  Result: No emails (before is exclusive)")
    
    # Next day for inclusive range
    next_day = datetime.strptime(same_day, "%Y/%m/%d") + timedelta(days=1)
    next_day_str = next_day.strftime("%Y/%m/%d")
    query2 = f'after:{same_day} before:{next_day_str}'
    print(f"Fixed same day: {query2}")
    print(f"  Result: Emails from {same_day}")

def analyze_user_case():
    """Analyze the specific user case"""
    print("\n=== User Case Analysis ===")
    
    user_start = "2025/01/01"
    user_end = "2025/06/30"
    actual_start = "2025/06/22"
    actual_end = "2025/06/29"
    
    print(f"User requested: {user_start} to {user_end}")
    print(f"Actual results: {actual_start} to {actual_end}")
    
    # Current query
    current = f'after:{user_start} before:{user_end}'
    print(f"Current query: {current}")
    
    # Analysis
    print("\nPossible issues:")
    print("1. Gmail 'before' is exclusive - emails on 2025/06/30 are excluded")
    print("2. Gmail may have different date interpretation or timezone issues")
    print("3. maxResults limit might be cutting off older emails")
    print("4. Gmail search might be returning most recent emails first")
    
    # Check if this could be a maxResults issue
    print(f"\nIf maxResults=1000 and there are >1000 emails in the range,")
    print(f"Gmail returns the most recent 1000, which could explain why")
    print(f"results are only from {actual_start} to {actual_end}")

def main():
    """Run all tests"""
    test_gmail_date_format()
    test_gmail_query_logic() 
    test_edge_cases()
    analyze_user_case()
    
    print("\n=== Recommended Fixes ===")
    print("1. Adjust end_date by adding 1 day for inclusive range")
    print("2. Add pagination to fetch ALL emails in range, not just first 1000")
    print("3. Add debugging output to show actual query sent to Gmail")
    print("4. Add date validation and timezone handling")

if __name__ == '__main__':
    main()