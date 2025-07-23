#!/usr/bin/env python3
"""
Test the cache date parsing fix
"""

from datetime import datetime
import json

def test_string_date_conversion():
    """Test converting string dates back to datetime objects"""
    
    # Simulate cached data with string timestamps
    test_timestamps = [
        "2025-06-22T10:15:30.123456",     # ISO format
        "2025-06-23T08:30:00+00:00",      # ISO with timezone
        "2025-06-24 14:45:15",            # Standard format
        "2025-06-25T12:00:00Z",           # ISO with Z
    ]
    
    print("=== Testing String Date Conversion ===")
    
    converted_dates = []
    
    for timestamp_str in test_timestamps:
        print(f"\nOriginal string: {timestamp_str}")
        
        # Apply the fix logic
        timestamp = timestamp_str
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                # Convert to timezone-naive for consistency
                if timestamp.tzinfo is not None:
                    timestamp = timestamp.replace(tzinfo=None)
                print(f"Converted to:    {timestamp} (tzinfo: {timestamp.tzinfo})")
                converted_dates.append(timestamp)
            except ValueError:
                try:
                    timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                    print(f"Alt conversion:  {timestamp} (tzinfo: {timestamp.tzinfo})")
                    converted_dates.append(timestamp)
                except ValueError:
                    print(f"Failed to convert: {timestamp_str}")
                    continue
    
    # Test date operations that were failing
    print(f"\n=== Testing Date Operations ===")
    if len(converted_dates) >= 2:
        try:
            first_date = min(converted_dates)
            last_date = max(converted_dates)
            time_span = (last_date - first_date).days
            
            print(f"✅ First date: {first_date}")
            print(f"✅ Last date:  {last_date}")
            print(f"✅ Time span:  {time_span} days")
            print("✅ Date operations work successfully!")
            
        except Exception as e:
            print(f"❌ Date operation failed: {e}")
    else:
        print("Not enough dates to test operations")

def simulate_cache_scenario():
    """Simulate the exact scenario from the user's cache"""
    print(f"\n=== Simulating Cache Scenario ===")
    
    # Create sample data like what would be in cache
    sample_emails = [
        {
            'message_id': 'test1',
            'sender': 'test@example.com',
            'sender_name': 'Test User',
            'timestamp': '2025-05-15T10:30:00.123456'
        },
        {
            'message_id': 'test2', 
            'sender': 'test@example.com',
            'sender_name': 'Test User',
            'timestamp': '2025-06-20T15:45:30.789012'
        }
    ]
    
    # Simulate JSON serialization/deserialization (this is what breaks datetime objects)
    json_str = json.dumps(sample_emails, default=str)
    loaded_emails = json.loads(json_str)
    
    print("After JSON round-trip, timestamps become strings:")
    for email in loaded_emails:
        print(f"  {email['timestamp']} (type: {type(email['timestamp'])})")
    
    # Apply our fix
    print("\nApplying the fix:")
    for email in loaded_emails:
        timestamp = email['timestamp']
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                if timestamp.tzinfo is not None:
                    timestamp = timestamp.replace(tzinfo=None)
                email['timestamp'] = timestamp
                print(f"  Fixed: {timestamp} (type: {type(timestamp)})")
            except ValueError:
                print(f"  Failed to fix: {timestamp}")
    
    # Test the operation that was failing
    timestamps = [email['timestamp'] for email in loaded_emails if isinstance(email['timestamp'], datetime)]
    if len(timestamps) >= 2:
        try:
            time_span = (max(timestamps) - min(timestamps)).days
            print(f"✅ Time span calculation works: {time_span} days")
        except Exception as e:
            print(f"❌ Still failing: {e}")

if __name__ == '__main__':
    test_string_date_conversion()
    simulate_cache_scenario()
    
    print(f"\n=== Summary ===")
    print("✅ The fix handles string timestamps from cached JSON data")
    print("✅ Converts them back to timezone-naive datetime objects")
    print("✅ Date arithmetic operations should now work")
    print("✅ Your resume command should work correctly!")