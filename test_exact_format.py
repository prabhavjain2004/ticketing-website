#!/usr/bin/env python
"""
Test with the exact title format from the database
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

def test_exact_format():
    """Test with exact format from database"""
    
    title = "WILDCARD- THE BEGINNING"  # Exact format from DB
    
    print(f"Testing exact title: '{title}'")
    print(f"Has dash separator: {has_dash_separator(title)}")
    print(f"Main part: '{split_title_main(title)}'")
    print(f"Subtitle part: '{split_title_subtitle(title)}'")
    
    print("\nThis will result in:")
    print(f"Main title on ticket: {split_title_main(title).upper()}")
    print(f"Subtitle on ticket: - {split_title_subtitle(title).upper()} -")

if __name__ == "__main__":
    test_exact_format()
