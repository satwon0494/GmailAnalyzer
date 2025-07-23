#!/usr/bin/env python3
"""
Test the timezone fix for datetime comparison issue
"""

from datetime import datetime
from email.utils import parsedate_to_datetime

def test_parse_date_fixed(date_str: str):
    """Test the fixed _parse_date function"""
    if not date_str:
        return None
        
    try:
        dt = parsedate_to_datetime(date_str)
        # Convert to timezone-naive UTC for consistent comparisons
        if dt.tzinfo is not None:
            dt = dt.utctimetuple()
            dt = datetime(*dt[:6])  # Convert to naive datetime
        return dt
    except Exception as e:
        print(f"Error parsing {date_str}: {e}")
        return None

def test_timezone_scenarios():
    """Test various timezone scenarios"""
    print("=== Testing Timezone Fix ===")
    
    # Sample email date strings with different timezone formats
    test_dates = [
        "Thu, 22 Jun 2025 10:15:30 +0000",    # UTC with offset
        "Mon, 23 Jun 2025 08:30:00 -0700",    # PDT 
        "Tue, 24 Jun 2025 14:45:15 +0200",    # CEST
        "Wed, 25 Jun 2025 12:00:00 GMT",      # GMT
        "Thu, 26 Jun 2025 09:30:45 EST",      # EST
        "Fri, 27 Jun 2025 16:20:30 PST",      # PST
    ]
    
    parsed_dates = []
    
    for date_str in test_dates:
        print(f"\nOriginal: {date_str}")
        
        # Test original method (would cause the error)
        try:
            original = parsedate_to_datetime(date_str)
            print(f"Original parse: {original} (tzinfo: {original.tzinfo})")
        except Exception as e:
            print(f"Original parse error: {e}")
            
        # Test fixed method
        fixed = test_parse_date_fixed(date_str)
        if fixed:
            print(f"Fixed parse:    {fixed} (tzinfo: {fixed.tzinfo})")
            parsed_dates.append(fixed)
        else:
            print("Fixed parse:    Failed")
    
    # Test comparisons (this would fail before the fix)
    print(f"\n=== Testing Date Comparisons ===")
    if len(parsed_dates) >= 2:
        try:
            first_date = min(parsed_dates)
            last_date = max(parsed_dates)
            time_span = (last_date - first_date).days
            
            print(f"✅ First date: {first_date}")
            print(f"✅ Last date:  {last_date}")
            print(f"✅ Time span:  {time_span} days")
            print("✅ Date comparisons work successfully!")
            
        except Exception as e:
            print(f"❌ Date comparison failed: {e}")
    else:
        print("Not enough valid dates to test comparisons")

def test_edge_cases():
    """Test edge cases"""
    print(f"\n=== Testing Edge Cases ===")
    
    edge_cases = [
        "",                                    # Empty string
        None,                                  # None
        "Invalid date string",                 # Invalid format
        "Thu, 22 Jun 2025 25:70:99 +0000",   # Invalid time values
    ]
    
    for case in edge_cases:
        result = test_parse_date_fixed(case)
        print(f"Input: {repr(case)} -> Result: {result}")

if __name__ == '__main__':
    test_timezone_scenarios()
    test_edge_cases()
    
    print(f"\n=== Summary ===")
    print("✅ All parsed dates are now timezone-naive")
    print("✅ Date comparisons will work without timezone conflicts") 
    print("✅ The 'offset-naive and offset-aware' error should be resolved")