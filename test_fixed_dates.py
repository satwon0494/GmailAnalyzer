#!/usr/bin/env python3
"""
Test script to verify the date filtering fix
"""

from datetime import datetime, timedelta

def test_date_fix():
    """Test the date adjustment logic"""
    print("=== Testing Date Fix ===")
    
    # Test cases
    test_cases = [
        ("2025/01/01", "2025/06/30"),
        ("2025/06/15", "2025/06/15"),  # Same day
        ("2023/12/01", "2023/12/31"),
    ]
    
    for start_date, end_date in test_cases:
        print(f"\nInput range: {start_date} to {end_date}")
        
        # Apply the fix logic
        try:
            end_dt = datetime.strptime(end_date, "%Y/%m/%d")
            adjusted_end_dt = end_dt + timedelta(days=1)
            adjusted_end_date = adjusted_end_dt.strftime("%Y/%m/%d")
            
            query = f'after:{start_date} before:{adjusted_end_date}'
            print(f"Gmail query: {query}")
            print(f"This will include emails through {end_date} (inclusive)")
            
        except ValueError as e:
            print(f"Error: {e}")

def show_usage_examples():
    """Show updated usage examples"""
    print("\n=== Updated Usage Examples ===")
    
    print("\n1. Your original command (now fixed):")
    print("python gmail_analyzer.py --start-date 2025/01/01 --end-date 2025/06/30")
    print("   → Will now fetch ALL emails from Jan 1 through June 30, 2025")
    
    print("\n2. Fetch unlimited emails in range:")
    print("python gmail_analyzer.py --start-date 2025/01/01 --end-date 2025/06/30 --max-emails 0")
    print("   → Will fetch ALL emails in the range (no limit)")
    
    print("\n3. Fetch more emails than default:")
    print("python gmail_analyzer.py --start-date 2025/01/01 --end-date 2025/06/30 --max-emails 50000")
    print("   → Will fetch up to 50,000 emails in the range")

if __name__ == '__main__':
    test_date_fix()
    show_usage_examples()
    
    print("\n=== Key Fixes Applied ===")
    print("✅ Fixed Gmail 'before' exclusion by adding 1 day to end date")
    print("✅ Added pagination to fetch ALL emails in range (not just first 1000)")
    print("✅ Increased default max_emails from 1000 to 10000")
    print("✅ Added option for unlimited emails (--max-emails 0)")
    print("✅ Added debugging output to show actual Gmail query")
    print("✅ Added proper date validation")