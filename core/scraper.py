"""
Enhanced main scraper class that coordinates all components.

This is an updated version of your core/scraper.py that uses the new modular components
while maintaining the same interface and following SOLID principles.
"""

import time
import random
from typing import List, Optional
from urllib.parse import urljoin
from datetime import datetime

from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException
from bs4 import BeautifulSoup

from core.models import CookieBannerAction, WebsiteAnalysisResult, Cookie, Screenshot, HttpUrl

# Import our new modular components
from core.browser_config import BrowserConfigurator, PageStabilityChecker
from core.cookie_collector import CookieCollector, CookieAnalyzer
from core.banner_detector import CookieBannerDetector


class WebsiteAnalyzer:
    """
    Enhanced website analyzer that coordinates all analysis components.
    
    This class follows the Open/Closed Principle - it's open for extension
    but closed for modification. The core logic is delegated to specialized classes.
    """
    
    def __init__(
        self, 
        url: str, 
        enable_anti_detection: bool = True, 
        max_retries: int = 3,
        headless: bool = False,
        language: str = "pt-PT"
    ):
        """
        Initializes the analyzer with enhanced configuration options.

        Args:
            url (str): The URL of the website to analyze.
            enable_anti_detection (bool): Whether to use anti-detection measures.
            max_retries (int): Maximum number of retry attempts for page loading.
            headless (bool): Whether to run in headless mode.
            language (str): Browser language setting.
        """
        self.url: str = url
        self.enable_anti_detection: bool = enable_anti_detection
        self.max_retries: int = max_retries
        self.headless: bool = headless
        self.language: str = language
        
        # Components - initialized when driver is created
        self.driver: Optional[webdriver.Chrome] = None
        self.stability_checker: Optional[PageStabilityChecker] = None
        self.cookie_collector: Optional[CookieCollector] = None
        self.banner_detector: Optional[CookieBannerDetector] = None

    def _setup_driver(self):
        """
        Initializes the WebDriver and associated components.
        
        Uses the BrowserConfigurator to create a properly configured driver.
        """
        try:
            print("🔧 Setting up enhanced WebDriver...")
            
            # Create Chrome options using the configurator
            chrome_options = BrowserConfigurator.create_chrome_options(
                headless=self.headless,
                enable_anti_detection=self.enable_anti_detection,
                language=self.language
            )
            
            # Create the driver
            self.driver = BrowserConfigurator.create_driver(chrome_options)
            
            # Apply anti-detection scripts if enabled
            if self.enable_anti_detection:
                BrowserConfigurator.apply_anti_detection_scripts(self.driver)
            
            # Initialize component classes
            self.stability_checker = PageStabilityChecker(self.driver)
            self.cookie_collector = CookieCollector(self.driver, self.url)
            self.banner_detector = CookieBannerDetector(self.driver)
            
            print("✅ Enhanced WebDriver setup completed successfully")
            
        except Exception as e:
            print(f"❌ Error setting up WebDriver: {e}")
            self.driver = None

    def _teardown_driver(self):
        """Safely closes the WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                print(f"⚠️ Error during driver teardown: {e}")

    def _load_page_with_retry(self) -> bool:
        """
        Loads the page with enhanced retry logic and stability checking.
        
        Returns:
            True if page loaded successfully, False otherwise.
        """
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    delay = self._calculate_retry_delay(attempt)
                    print(f"🔄 Retry attempt {attempt + 1}/{self.max_retries}, waiting {delay:.1f}s...")
                    time.sleep(delay)
                    
                    # Clear browser state on retry
                    self._clear_browser_state()
                
                print(f"🌐 Loading page (attempt {attempt + 1})...")
                self.driver.get(self.url)
                
                # Wait for page stability using the dedicated checker
                self.stability_checker.wait_for_stability()
                
                # Verify page loaded properly
                if (self.stability_checker.is_page_loaded_properly() and 
                    not self.stability_checker.is_page_blocked()):
                    print("✅ Page loaded successfully")
                    return True
                else:
                    print(f"⚠️ Page issues detected on attempt {attempt + 1}")
                    if self.stability_checker.is_page_blocked():
                        print("   Page appears to be blocked by security system")
                    continue
                    
            except Exception as e:
                print(f"❌ Error loading page on attempt {attempt + 1}: {e}")
                
        print(f"❌ Failed to load page after {self.max_retries} attempts")
        return False

    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculates retry delay with reduced times for better performance."""
        base_delay = random.uniform(2, 5)  # Reduced from 5-15 to 2-5
        exponential_factor = 1.5 ** (attempt - 1)  # Reduced from 2 to 1.5
        delay = base_delay * exponential_factor
        return min(delay, 15)  # Cap at 15 seconds instead of potentially much higher
        return min(delay, 60)  # Cap at 60 seconds

    def _clear_browser_state(self):
        """Clears browser state between retries."""
        try:
            self.driver.delete_all_cookies()
            self.driver.execute_script("window.localStorage.clear();")
            self.driver.execute_script("window.sessionStorage.clear();")
        except Exception as e:
            print(f"⚠️ Error clearing browser state: {e}")

    def _take_screenshot(self, screenshot_type: str) -> Optional[Screenshot]:
        """
        Takes a screenshot with enhanced error handling.
        
        Args:
            screenshot_type: Type identifier for the screenshot
            
        Returns:
            Screenshot object or None if failed
        """
        try:
            # Scroll to top for consistent screenshots
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            base64_data = self.driver.get_screenshot_as_base64()
            size_kb = len(base64_data) / 1024
            print(f"📸 Screenshot taken: {screenshot_type} ({size_kb:.1f} KB)")
            
            return Screenshot(screenshot_type=screenshot_type, base64_data=base64_data)
            
        except Exception as e:
            print(f"❌ Error taking screenshot '{screenshot_type}': {e}")
            return None

    def _find_policy_urls(self) -> tuple[Optional[HttpUrl], Optional[HttpUrl]]:
        """
        Finds privacy and cookie policy URLs using enhanced detection.
        
        Returns:
            Tuple of (privacy_policy_url, cookie_policy_url)
        """
        print("🔍 Searching for policy URLs...")
        
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            policy_keywords = {
                "privacy": [
                    "privacy policy", "privacy", "data policy", "data protection",
                    "privacidade", "política de privacidade", "proteção de dados",
                    "protecção de dados", "rgpd", "gdpr", "aviso de privacidade"
                ],
                "cookie": [
                    "cookie policy", "cookies policy", "cookie notice", "cookies",
                    "política de cookies", "aviso de cookies", "gestão de cookies",
                    "informação cookies", "sobre cookies", "declaração cookies"
                ]
            }
            
            privacy_url = self._find_policy_url(soup, policy_keywords["privacy"])
            cookie_url = self._find_policy_url(soup, policy_keywords["cookie"])
            
            if privacy_url:
                print(f"📋 Privacy policy found: {privacy_url}")
            if cookie_url:
                print(f"🍪 Cookie policy found: {cookie_url}")
                
            return privacy_url, cookie_url
            
        except Exception as e:
            print(f"❌ Error finding policy URLs: {e}")
            return None, None

    def _find_policy_url(self, soup, keywords: List[str]) -> Optional[HttpUrl]:
        """Helper method to find a specific policy URL."""
        for link in soup.find_all('a', href=True):
            text = link.get_text().strip().lower()
            href = link.get('href', '').strip()
            title = link.get('title', '').strip().lower()
            
            all_text = f"{text} {title}"
            
            for keyword in keywords:
                if keyword in all_text or keyword in href.lower():
                    full_url = urljoin(self.url, href)
                    return HttpUrl(full_url)
        
        return None

    def _print_analysis_summary(self, result: WebsiteAnalysisResult):
        """
        Prints an enhanced analysis summary.
        
        Args:
            result: The analysis result to summarize
        """
        print("\n" + "="*60)
        print("📊 ANALYSIS SUMMARY")
        print("="*60)
        print(f"🌐 URL: {result.url}")
        print(f"📅 Timestamp: {result.analysis_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🍪 Cookie Banner: {'✅ Found' if result.has_cookie_banner else '❌ Not found'}")
        
        if result.cookie_banner_action:
            print(f"🎯 Action Taken: {result.cookie_banner_action}")
        
        # Policy URLs
        print(f"📋 Privacy Policy: {'✅ Found' if result.privacy_policy_url else '❌ Not found'}")
        print(f"🍪 Cookie Policy: {'✅ Found' if result.cookie_policy_url else '❌ Not found'}")
        
        # Cookie analysis
        print(f"🍪 Total Cookies: {len(result.cookies)}")
        if result.cookies:
            # Use the cookie analyzer for insights
            categories = CookieAnalyzer.categorize_cookies(result.cookies)
            print(f"   🔒 Secure: {len(categories['secure'])}")
            print(f"   🚫 HttpOnly: {len(categories['http_only'])}")
            print(f"   ⏰ Session: {len(categories['session'])}")
            print(f"   💾 Persistent: {len(categories['persistent'])}")
        
        print(f"📸 Screenshots: {len(result.screenshots)}")
        print("="*60)

    def analyze(self, action: CookieBannerAction = CookieBannerAction.NONE) -> Optional[WebsiteAnalysisResult]:
        """
        Performs comprehensive website analysis using modular components.
        
        Args:
            action: The cookie banner action to perform
            
        Returns:
            WebsiteAnalysisResult object or None if analysis failed
        """
        print(f"🚀 Starting enhanced analysis for {self.url}")
        
        # Setup
        self._setup_driver()
        if not self.driver:
            print("❌ Failed to setup driver")
            return None

        try:
            # Load page with retry logic
            if not self._load_page_with_retry():
                print("⚠️ WARNING: Page loading issues detected, continuing with limited analysis")

            # Print page information for debugging
            try:
                print(f"📄 Page title: {self.driver.title}")
                print(f"🌐 Current URL: {self.driver.current_url}")
            except Exception:
                print("❌ Could not retrieve page information")

            # Take initial screenshot
            screenshots = []
            initial_screenshot = self._take_screenshot("initial")
            if initial_screenshot:
                screenshots.append(initial_screenshot)

            # Collect initial cookies
            print("\n🍪 Collecting initial cookies...")
            initial_cookies = self.cookie_collector.collect_cookies("initial")

            # Handle cookie banner interaction
            has_cookie_banner = False
            cookie_banner_action = None
            final_cookies = initial_cookies

            if action != CookieBannerAction.NONE:
                print(f"\n🎯 Attempting cookie banner interaction: {action.value}")
                cookie_banner_action = self.banner_detector.detect_and_interact(action)
                has_cookie_banner = self.banner_detector.banner_found

                if has_cookie_banner and cookie_banner_action:
                    print("⏳ Waiting for cookie changes to take effect...")
                    time.sleep(5)
                    
                    # Take post-interaction screenshot
                    post_screenshot = self._take_screenshot("post_interaction")
                    if post_screenshot:
                        screenshots.append(post_screenshot)
                    
                    # Collect post-interaction cookies
                    print("\n🍪 Collecting post-interaction cookies...")
                    post_cookies = self.cookie_collector.collect_cookies("post_interaction")
                    
                    # Analyze cookie changes
                    changes = CookieAnalyzer.analyze_cookie_changes(initial_cookies, post_cookies)
                    print(f"📊 Cookie changes: +{len(changes['added_cookies'])} added, "
                          f"{len(changes['changed_cookies'])} modified")
                    
                    final_cookies = post_cookies

            # Find policy URLs
            privacy_url, cookie_url = self._find_policy_urls()

            # Create result
            result = WebsiteAnalysisResult(
                url=HttpUrl(self.url),
                analysis_timestamp=datetime.now(),
                has_cookie_banner=has_cookie_banner,
                cookie_banner_action=cookie_banner_action,
                privacy_policy_url=privacy_url,
                cookie_policy_url=cookie_url,
                cookies=final_cookies,
                screenshots=screenshots
            )

            # Print summary
            self._print_analysis_summary(result)

            return result

        except (WebDriverException, TimeoutException) as e:
            print(f"❌ WebDriver error during analysis: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error during analysis: {e}")
            return None
        finally:
            self._teardown_driver()

    def _analyze_with_existing_driver(self, action: CookieBannerAction = CookieBannerAction.NONE) -> Optional[WebsiteAnalysisResult]:
        """
        Optimized analysis method that reuses the existing driver session.
        This method assumes the driver is already set up and doesn't teardown afterwards.
        
        Args:
            action: The cookie banner action to perform
            
        Returns:
            WebsiteAnalysisResult object or None if analysis failed
        """
        if not self.driver:
            print("❌ No driver available for analysis")
            return None

        try:
            # Clear any previous state but keep the driver alive
            try:
                self.driver.delete_all_cookies()
                self.driver.execute_script("window.localStorage.clear(); window.sessionStorage.clear();")
            except Exception as e:
                print(f"⚠️ Warning: Could not clear browser state: {e}")
            
            # Load page with reduced retry logic for speed
            if not self._load_page_with_retry():
                print("⚠️ WARNING: Page loading issues detected, continuing with limited analysis")

            # Print page information for debugging
            try:
                print(f"📄 Page title: {self.driver.title}")
                print(f"🌐 Current URL: {self.driver.current_url}")
            except Exception:
                print("❌ Could not retrieve page information")

            # Take initial screenshot
            screenshots = []
            initial_screenshot = self._take_screenshot("initial")
            if initial_screenshot:
                screenshots.append(initial_screenshot)

            # Collect initial cookies
            print("\n🍪 Collecting initial cookies...")
            initial_cookies = self.cookie_collector.collect_cookies("initial")

            # Handle cookie banner interaction
            has_cookie_banner = False
            cookie_banner_action = None
            final_cookies = initial_cookies

            if action != CookieBannerAction.NONE:
                print(f"\n🎯 Attempting cookie banner interaction: {action.value}")
                cookie_banner_action = self.banner_detector.detect_and_interact(action)
                has_cookie_banner = self.banner_detector.banner_found

                if has_cookie_banner and cookie_banner_action:
                    print("⏳ Waiting for cookie changes to take effect...")
                    time.sleep(3)  # Reduced wait time from 5 to 3 seconds
                    
                    # Take post-interaction screenshot
                    post_screenshot = self._take_screenshot("post_interaction")
                    if post_screenshot:
                        screenshots.append(post_screenshot)
                    
                    # Collect post-interaction cookies
                    print("\n🍪 Collecting post-interaction cookies...")
                    post_cookies = self.cookie_collector.collect_cookies("post_interaction")
                    
                    # Analyze cookie changes
                    changes = CookieAnalyzer.analyze_cookie_changes(initial_cookies, post_cookies)
                    print(f"📊 Cookie changes: +{len(changes['added_cookies'])} added, "
                          f"{len(changes['changed_cookies'])} modified")
                    
                    final_cookies = post_cookies

            # Find policy URLs
            privacy_url, cookie_url = self._find_policy_urls()

            # Create result
            result = WebsiteAnalysisResult(
                url=HttpUrl(self.url),
                analysis_timestamp=datetime.now(),
                has_cookie_banner=has_cookie_banner,
                cookie_banner_action=cookie_banner_action,
                privacy_policy_url=privacy_url,
                cookie_policy_url=cookie_url,
                cookies=final_cookies,
                screenshots=screenshots
            )

            # Print summary
            self._print_analysis_summary(result)

            return result

        except (WebDriverException, TimeoutException) as e:
            print(f"❌ WebDriver error during analysis: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error during analysis: {e}")
            return None
        # Note: No finally block here - driver is kept alive intentionally


# Backward compatibility - keep the same interface as your existing main.py
if __name__ == "__main__":
    # Simple test
    test_url = "https://www.cm-beja.pt/"
    analyzer = WebsiteAnalyzer(test_url, headless=False)
    result = analyzer.analyze(action=CookieBannerAction.ACCEPT_ALL)
    
    if result:
        print(f"✅ Analysis completed with {len(result.cookies)} cookies collected")
    else:
        print("❌ Analysis failed")