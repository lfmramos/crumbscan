"""
Production-ready optimized main script with headless mode and minimal browser operations.
No visible browser windows, maximum speed.
"""
import os
from typing import List
import time

from core.scraper import WebsiteAnalyzer
from database.db_manager import DatabaseManager
from core.models import CookieBannerAction


def read_websites_from_file(file_path: str) -> List[str]:
    """
    Reads a list of website URLs from a specified file,
    skipping any blank lines or comments.
    """
    websites = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    websites.append(line)
    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found.")
        return []
    except IOError as e:
        print(f"Error reading the file '{file_path}': {e}")
        return []
    return websites


def main():
    """
    Production-optimized main function with headless browser and minimal operations.
    No visible browser windows, maximum performance.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'data', 'websites.txt')

    print(f"Reading websites from {file_path}...")
    website_urls = read_websites_from_file(file_path)

    if not website_urls:
        print("No websites to analyze. Please check the 'websites.txt' file.")
        return

    # Initialize the database manager
    db_path = os.path.join(current_dir, 'data_protection_results.db')
    db_manager = DatabaseManager(db_path)
    print(f"Database initialized at {db_path}")

    # Define the actions to perform for each website
    actions = [CookieBannerAction.ACCEPT_ALL, CookieBannerAction.REJECT_ALL, CookieBannerAction.NONE]
    
    print("\n🚀 Starting HEADLESS production analysis...")
    print("ℹ️  No browser windows will be shown for maximum performance")
    
    # Process each website URL with production optimization
    for url in website_urls:
        print("\n" + "="*50)
        print(f"Analyzing: {url}")
        
        # Create ONE analyzer instance per website with headless mode
        analyzer = WebsiteAnalyzer(
            url, 
            enable_anti_detection=True,  # Keep anti-detection for better success rate
            max_retries=1,  # Minimal retries for speed
            headless=True,  # 🔑 KEY: Run in headless mode (no visible windows)
            language="pt-PT"
        )
        
        try:
            # Setup browser once (headless)
            analyzer._setup_driver()
            
            if not analyzer.driver:
                print(f"❌ Failed to setup headless driver for {url}, skipping...")
                continue
            
            print("✅ Headless browser ready")
            
            for i, action in enumerate(actions, 1):
                print(f"\n--- Scenario {i}/3: {action.value} ---")
                
                try:
                    # Use internal method to avoid recreating driver
                    analysis_result = analyzer._analyze_with_existing_driver(action=action)
                    
                    if analysis_result:
                        cookie_count = len(analysis_result.cookies)
                        banner_status = "✅ Found" if analysis_result.has_cookie_banner else "❌ Not found"
                        print(f"✅ Complete: {cookie_count} cookies | Banner: {banner_status}")
                        db_manager.insert_analysis_result(analysis_result)
                    else:
                        print(f"❌ Analysis failed for scenario '{action.value}'")
                        
                except Exception as e:
                    print(f"❌ Error in scenario '{action.value}': {str(e)[:50]}...")
                    
        except Exception as e:
            print(f"❌ Critical error processing '{url}': {str(e)[:50]}...")
        finally:
            # Clean up browser after all scenarios for this website
            try:
                analyzer._teardown_driver()
                print("🔧 Browser session closed")
            except:
                pass
    
    print("\n" + "="*50)
    print("🎉 All websites processed in HEADLESS mode!")
    
    # Print summary statistics
    try:
        total_results = len([f for f in os.listdir(current_dir) if f.endswith('.db')])
        print(f"\n📊 Analysis complete - check database for {total_results} results")
    except:
        print("📊 Analysis complete - check database for results")


if __name__ == "__main__":
    main()
