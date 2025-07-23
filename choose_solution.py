#!/usr/bin/env python3
"""
Gmail Analyzer Solution Selector
Helps you choose the best approach for your specific needs
"""

def main():
    print("🔍 Gmail Analyzer Solution Selector")
    print("=" * 50)
    
    # Ask key questions
    print("\\nLet's find the best solution for your needs:\\n")
    
    # Question 1: Dataset size
    print("1. How many emails do you need to analyze?")
    print("   a) < 10,000 emails")
    print("   b) 10,000 - 50,000 emails") 
    print("   c) 50,000 - 200,000 emails")
    print("   d) 200,000+ emails")
    
    size_choice = input("\\nYour choice (a/b/c/d): ").lower().strip()
    
    # Question 2: Use case
    print("\\n2. What's your primary use case?")
    print("   a) One-time historical analysis")
    print("   b) Ongoing monitoring/updates")
    print("   c) Real-time email tracking")
    print("   d) Cost is most important factor")
    
    use_case = input("\\nYour choice (a/b/c/d): ").lower().strip()
    
    # Question 3: Technical comfort
    print("\\n3. Your technical comfort level?")
    print("   a) Beginner - want simplest solution")
    print("   b) Intermediate - comfortable with setup")
    print("   c) Advanced - want maximum control")
    
    tech_level = input("\\nYour choice (a/b/c): ").lower().strip()
    
    # Generate recommendation
    print("\\n" + "=" * 50)
    print("🎯 RECOMMENDATION FOR YOU")
    print("=" * 50)
    
    # Logic for recommendation
    if size_choice in ['c', 'd'] and use_case in ['a', 'd']:
        # Large dataset, one-time or cost-sensitive
        print("\\n🚀 **PRIMARY RECOMMENDATION: Gmail Takeout**")
        print("   File: gmail_takeout_analyzer.py")
        print("   Why: Ultra-fast (40k+ emails/min), zero cost, perfect for large historical analysis")
        print("\\n📋 Setup steps:")
        print("   1. pip install -r requirements_takeout.txt")
        print("   2. Go to https://takeout.google.com → Gmail export")
        print("   3. Wait for download link (2-24 hours)")
        print("   4. python gmail_takeout_analyzer.py /path/to/takeout")
        print("\\n📖 Full guide: QUICK_START_TAKEOUT.md")
        
    elif use_case in ['b', 'c']:
        # Ongoing or real-time needs
        print("\\n⚡ **PRIMARY RECOMMENDATION: Optimized Gmail API**")
        print("   File: gmail_api_optimized.py")
        print("   Why: Real-time capable, smart caching, 10x faster than original")
        print("\\n📋 Setup steps:")
        print("   1. pip install -r requirements_optimized.txt")
        print("   2. python gmail_api_optimized.py --start-date YYYY/MM/DD --end-date YYYY/MM/DD")
        print("\\n💰 Cost: Usually free (within Gmail API limits)")
        
    elif tech_level == 'c':
        # Advanced users
        print("\\n🌐 **RECOMMENDATION: IMAP Solution**")
        print("   File: gmail_imap_analyzer.py")
        print("   Why: Direct protocol access, no API costs, good for custom integration")
        print("\\n📋 Setup steps:")
        print("   1. pip install -r requirements_optimized.txt")
        print("   2. Enable IMAP in Gmail settings")
        print("   3. python gmail_imap_analyzer.py --start-date YYYY/MM/DD --end-date YYYY/MM/DD")
        
    else:
        # Default to takeout for large datasets, optimized API for smaller
        if size_choice in ['c', 'd']:
            print("\\n🚀 **RECOMMENDATION: Gmail Takeout**")
            print("   Best for your large dataset - see QUICK_START_TAKEOUT.md")
        else:
            print("\\n⚡ **RECOMMENDATION: Optimized Gmail API**")
            print("   Good balance of speed and features for your dataset size")
    
    # Performance comparison
    print("\\n" + "=" * 50)
    print("📊 PERFORMANCE COMPARISON")
    print("=" * 50)
    
    if size_choice == 'd':  # 200k+ emails
        print("\\nFor your 200k+ emails:")
        print("🚀 Takeout:        ~5-10 minutes   ($0)")
        print("⚡ Optimized API:  ~30-50 minutes  ($0-50)")
        print("🌐 IMAP:           ~40-100 minutes ($0)")
        print("❌ Original:       ~25+ hours      ($200+)")
        
    elif size_choice == 'c':  # 50k-200k emails  
        print("\\nFor your 50k-200k emails:")
        print("🚀 Takeout:        ~1-5 minutes    ($0)")
        print("⚡ Optimized API:  ~10-25 minutes  ($0)")
        print("🌐 IMAP:           ~15-50 minutes  ($0)")
        print("❌ Original:       ~6-25 hours     ($50+)")
        
    else:
        print("\\nFor your dataset size:")
        print("🚀 Takeout:        <1 minute       ($0)")
        print("⚡ Optimized API:  ~2-10 minutes   ($0)")
        print("🌐 IMAP:           ~5-20 minutes   ($0)")
        print("✅ Original:       30min-3hours    ($0)")
    
    print("\\n💡 Need help? Check PERFORMANCE_COMPARISON.md for detailed analysis!")
    
if __name__ == '__main__':
    main()