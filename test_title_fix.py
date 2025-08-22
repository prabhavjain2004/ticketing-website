#!/usr/bin/env python
"""
Test script to verify the event title parsing functions work correctly
"""
import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tapnex_ticketing_system.settings')
django.setup()

from ticketing.templatetags.ticketing_extras import split_title_main, split_title_subtitle, has_dash_separator

def test_title_parsing():
    """Test our custom template filters"""
    
    test_cases = [
        "WILDCARD - THE BEGINNING",
        "Summer Music Fest - The Ultimate Experience",
        "Tech Conference 2024",
        "Workshop - Advanced Python",
        "Event Name - Part 1 - Special Edition",
    ]
    
    print("Testing Event Title Parsing Functions:")
    print("=" * 50)
    
    for title in test_cases:
        print(f"Original Title: '{title}'")
        print(f"Has dash separator: {has_dash_separator(title)}")
        print(f"Main part: '{split_title_main(title)}'")
        print(f"Subtitle part: '{split_title_subtitle(title)}'")
        print("-" * 30)

if __name__ == "__main__":
    test_title_parsing()
