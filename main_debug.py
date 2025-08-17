"""
Debug version with visible browser windows for troubleshooting.
Use this only when you need to see what's happening in the browser.
"""
import os
from typing import List

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
    Debug version with visible browser windows for troubleshooting.
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
    
    print("\n🔍 Starting DEBUG analysis with visible browser...")
    print("⚠️  Browser windows will be shown for debugging purposes")
    input("Press Enter to continue or Ctrl+C to cancel...")
    
    # Process each website URL with debug settings
    for url in website_urls:
        print("\n" + "="*50)
        print(f"🐛 DEBUG MODE - Analyzing: {url}")
        
        # Create analyzer with visible browser for debugging
        analyzer = WebsiteAnalyzer(
            url, 
            enable_anti_detection=True,
            max_retries=2,
            headless=False,  # 🔑 Show browser for debugging
            language="pt-PT"
        )
        
        try:
            # Setup browser once
            analyzer._setup_driver()
            
            if not analyzer.driver:
                print(f"❌ Failed to setup driver for {url}, skipping...")
                continue
            
            print("🔍 Browser window is now visible for debugging")
            
            for action in actions:
                print(f"\n--- 🐛 DEBUG: Running scenario: {action.value} ---")
                input(f"Press Enter to run '{action.value}' scenario or Ctrl+C to skip...")
                
                try:
                    # Use internal method to avoid recreating driver
                    analysis_result = analyzer._analyze_with_existing_driver(action=action)
                    
                    if analysis_result:
                        print(f"✅ Debug complete: {len(analysis_result.cookies)} cookies collected")
                        print(f"🎯 Banner found: {analysis_result.has_cookie_banner}")
                        db_manager.insert_analysis_result(analysis_result)
                        input("Press Enter to continue to next scenario...")
                    else:
                        print(f"❌ Analysis failed for '{url}' with action '{action.value}'")
                        
                except Exception as e:
                    print(f"❌ Error analyzing '{url}' with action '{action.value}': {e}")
                    input("Press Enter to continue despite error...")
                    
        except Exception as e:
            print(f"❌ Critical error processing '{url}': {e}")
        finally:
            # Clean up browser after all scenarios for this website
            try:
                analyzer._teardown_driver()
                print("🔧 Debug browser session closed")
            except:
                pass
    
    print("\n" + "="*50)
    print("🐛 Debug analysis complete!")


if __name__ == "__main__":
    main()
