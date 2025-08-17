"""
Super optimized main script with even better cookie collection and performance.
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


def warm_up_browser(analyzer):
    """
    Warms up the browser by visiting common tracking domains first.
    This helps establish cookies that would normally be there in a real session.
    """
    print("🔥 Warming up browser with common tracking domains...")
    
    warmup_sites = [
        "https://www.google.com/",
        "https://analytics.google.com/",  
        "https://www.facebook.com/"
    ]
    
    for site in warmup_sites:
        try:
            print(f"  📡 Visiting {site}...")
            analyzer.driver.get(site)
            time.sleep(2)  # Brief wait
        except Exception as e:
            print(f"  ⚠️ Warmup failed for {site}: {e}")
            continue
    
    print("✅ Browser warmup completed")


def main():
    """
    Super optimized main function with browser warmup and enhanced cookie collection.
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
    
    # Process each website URL with super optimization
    for url in website_urls:
        print("\n" + "="*50)
        print(f"Starting SUPER OPTIMIZED analysis for: {url}")
        
        # Create ONE analyzer instance per website
        analyzer = WebsiteAnalyzer(
            url, 
            enable_anti_detection=False,  # Disable to speed up - may help with cookie collection
            max_retries=1,  # Further reduced retries for speed
            headless=True,  # Use headless mode for production (no visible windows)
            language="pt-PT"
        )
        
        try:
            # Setup browser once
            analyzer._setup_driver()
            
            if not analyzer.driver:
                print(f"❌ Failed to setup driver for {url}, skipping...")
                continue
            
            # Warm up browser to establish tracking cookies
            warm_up_browser(analyzer)
            
            for action in actions:
                print(f"\n--- Running scenario: {action.value} ---")
                
                try:
                    # Use internal method to avoid recreating driver
                    analysis_result = analyzer._analyze_with_existing_driver(action=action)
                    
                    if analysis_result:
                        print(f"✅ Analysis complete: {len(analysis_result.cookies)} cookies collected")
                        print(f"📊 Action '{action.value}' results saved to database")
                        db_manager.insert_analysis_result(analysis_result)
                    else:
                        print(f"❌ Analysis failed for '{url}' with action '{action.value}'")
                        
                except Exception as e:
                    print(f"❌ Error analyzing '{url}' with action '{action.value}': {e}")
                    
        except Exception as e:
            print(f"❌ Critical error processing '{url}': {e}")
        finally:
            # Clean up browser after all scenarios for this website
            try:
                analyzer._teardown_driver()
            except:
                pass
    
    print("\n" + "="*50)
    print("🎉 All websites processed with SUPER OPTIMIZATION!")
    
    # Print summary statistics
    try:
        summary_stats = db_manager.get_summary_statistics()
        print("\n📈 SUMMARY STATISTICS:")
        print(f"  📊 Total analyses: {summary_stats.get('total_analyses', 0)}")
        print(f"  🍪 Total cookies collected: {summary_stats.get('total_cookies', 0)}")
        print(f"  🎯 Cookie banners found: {summary_stats.get('banners_found', 0)}")
    except:
        print("📊 Summary statistics not available")


if __name__ == "__main__":
    main()
