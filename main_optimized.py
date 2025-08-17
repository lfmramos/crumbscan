import os
from typing import List

from core.scraper import WebsiteAnalyzer
from database.db_manager import DatabaseManager
from core.models import CookieBannerAction


def read_websites_from_file(file_path: str) -> List[str]:
    """
    Reads a list of website URLs from a specified file,
    skipping any blank lines or comments.

    Args:
        file_path (str): The path to the file containing the URLs.

    Returns:
        List[str]: A list of clean website URLs.
    """
    websites = []
    try:
        # Using 'with' is a clean way to ensure the file is always closed.
        with open(file_path, 'r') as file:
            for line in file:
                # Remove leading/trailing whitespace and skip comments or empty lines.
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
    Optimized main function to orchestrate the data protection analysis.
    Uses a single WebDriver instance per website instead of per scenario.
    """
    # Get the directory of the current script and construct the file path
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
    
    # Process each website URL with optimized approach
    for url in website_urls:
        print("\n" + "="*50)
        print(f"Starting optimized multi-scenario analysis for: {url}")
        
        # Create ONE analyzer instance per website to reuse browser session
        analyzer = WebsiteAnalyzer(
            url, 
            enable_anti_detection=True, 
            max_retries=2,  # Reduced retries
            headless=True,  # Use headless mode for production (no visible windows)
            language="pt-PT"
        )
        
        try:
            # Setup browser once
            analyzer._setup_driver()
            
            if not analyzer.driver:
                print(f"❌ Failed to setup driver for {url}, skipping...")
                continue
            
            for action in actions:
                print(f"\n--- Running scenario: {action.value} ---")
                
                try:
                    # Use internal method to avoid recreating driver
                    analysis_result = analyzer._analyze_with_existing_driver(action=action)
                    
                    if analysis_result:
                        print(f"Analysis for action '{action.value}' complete. Inserting results into the database...")
                        db_manager.insert_analysis_result(analysis_result)
                    else:
                        print(f"Analysis failed for '{url}' with action '{action.value}'. Skipping database insertion.")
                        
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
    print("All websites processed.")


if __name__ == "__main__":
    main()
