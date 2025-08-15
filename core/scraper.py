import time
import random
from typing import List, Optional
from urllib.parse import urljoin
import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from core.models import CookieBannerAction, WebsiteAnalysisResult, Cookie, Screenshot, HttpUrl
from datetime import datetime


class WebsiteAnalyzer:
    """
    Analyzes a single website to check for a cookie banner,
    collect cookies before and after interaction, and find policy URLs.
    """
    def __init__(self, url: str, enable_anti_detection: bool = True, max_retries: int = 3):
        """
        Initializes the analyzer with the target URL.

        Args:
            url (str): The URL of the website to analyze.
            enable_anti_detection (bool): Whether to use anti-detection measures.
            max_retries (int): Maximum number of retry attempts for page loading.
        """
        self.url: str = url
        self.driver: Optional[webdriver.Chrome] = None
        self.enable_anti_detection: bool = enable_anti_detection
        self.max_retries: int = max_retries
        # Tracks whether any cookie banner was found during the last interaction
        self._banner_found: bool = False

    def _setup_driver(self):
        """
        Initializes and configures the Selenium WebDriver with anti-detection measures.
        """
        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            # Anti-detection measures (only if enabled)
            if self.enable_anti_detection:
                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                chrome_options.add_experimental_option('useAutomationExtension', False)
                
                # More realistic user agent
                chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                
                # Additional headers to avoid detection
                chrome_options.add_argument("--accept-lang=en-US,en;q=0.9")
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--disable-plugins")
                chrome_options.add_argument("--disable-images")  # Speed up loading
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to remove webdriver property (only if anti-detection enabled)
            if self.enable_anti_detection:
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.driver.set_page_load_timeout(30)
        except Exception as e:
            print(f"Error setting up WebDriver: {e}")
            self.driver = None

    def _teardown_driver(self):
        """
        Quits the WebDriver instance if it exists.
        """
        if self.driver:
            self.driver.quit()

    def _is_page_blocked(self) -> bool:
        """
        Detects if the current page is blocked by a security system.
        
        Returns:
            bool: True if the page is blocked, False otherwise.
        """
        if not self.driver:
            return False
            
        try:
            page_source = self.driver.page_source.lower()
            page_title = self.driver.title.lower()
            
            # Common blocked page indicators
            blocked_indicators = [
                "web page blocked",
                "access denied",
                "blocked by",
                "security warning",
                "attack id",
                "client ip",
                "message id",
                "page cannot be displayed",
                "contact the administrator",
                "forbidden",
                "unauthorized access",
                "security policy",
                "waf",
                "web application firewall"
            ]
            
            # Check page source and title for blocked indicators
            for indicator in blocked_indicators:
                if indicator in page_source or indicator in page_title:
                    return True
                    
            return False
            
        except Exception as e:
            print(f"Error checking if page is blocked: {e}")
            return False

    def _is_page_loaded_properly(self) -> bool:
        """
        Checks if the page has loaded properly with actual content.
        
        Returns:
            bool: True if page loaded properly, False otherwise.
        """
        if not self.driver:
            return False
            
        try:
            # Check if page has meaningful content
            page_source = self.driver.page_source
            body_text = self.driver.find_element(By.TAG_NAME, "body").text.strip()
            
            # If page is too short or contains mostly error messages, it's probably not loaded properly
            if len(page_source) < 1000 or len(body_text) < 100:
                return False
                
            # Check for common error page patterns
            error_patterns = [
                "error", "not found", "cannot", "blocked", "denied", "forbidden",
                "maintenance", "down", "unavailable", "timeout"
            ]
            
            page_lower = page_source.lower()
            error_count = sum(1 for pattern in error_patterns if pattern in page_lower)
            
            # If too many error indicators, page probably didn't load properly
            return error_count < 3
            
        except Exception as e:
            print(f"Error checking if page loaded properly: {e}")
            return False

    def _load_page_with_retry(self) -> bool:
        """
        Loads the page with retry logic and random delays to avoid detection.
        
        Returns:
            bool: True if page loaded successfully, False otherwise.
        """
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    # Random delay between retries (2-8 seconds)
                    delay = random.uniform(2, 8)
                    print(f"Retry attempt {attempt + 1}/{self.max_retries}, waiting {delay:.1f}s...")
                    time.sleep(delay)
                
                print(f"Loading page (attempt {attempt + 1})...")
                self.driver.get(self.url)
                
                # Random wait time to simulate human behavior (5-12 seconds)
                wait_time = random.uniform(5, 12)
                print(f"Waiting {wait_time:.1f}s for page to load...")
                time.sleep(wait_time)
                
                # Check if page loaded properly
                if self._is_page_loaded_properly() and not self._is_page_blocked():
                    print("✅ Page loaded successfully")
                    return True
                else:
                    print(f"⚠️  Page may not have loaded properly on attempt {attempt + 1}")
                    if self._is_page_blocked():
                        print("   Page appears to be blocked by security system")
                    
            except Exception as e:
                print(f"Error loading page on attempt {attempt + 1}: {e}")
                
        print(f"❌ Failed to load page properly after {self.max_retries} attempts")
        return False

    def _get_blocked_page_info(self) -> dict:
        """
        Extracts information from blocked pages to help with debugging.
        
        Returns:
            dict: Information about the blocked page including reason, IP, etc.
        """
        if not self.driver:
            return {}
            
        try:
            page_source = self.driver.page_source
            page_title = self.driver.title
            
            info = {
                "title": page_title,
                "blocked": True,
                "reason": "Unknown",
                "client_ip": None,
                "attack_id": None,
                "message_id": None
            }
            
            # Try to extract specific information from blocked pages
            if "attack id" in page_source.lower():
                # Look for attack ID pattern
                import re
                attack_match = re.search(r'attack id[:\s]*(\d+)', page_source, re.IGNORECASE)
                if attack_match:
                    info["attack_id"] = attack_match.group(1)
                    
            if "client ip" in page_source.lower():
                # Look for client IP pattern
                ip_match = re.search(r'client ip[:\s]*([\d\.]+)', page_source, re.IGNORECASE)
                if ip_match:
                    info["client_ip"] = ip_match.group(1)
                    
            if "message id" in page_source.lower():
                # Look for message ID pattern
                msg_match = re.search(r'message id[:\s]*(\d+)', page_source, re.IGNORECASE)
                if msg_match:
                    info["message_id"] = msg_match.group(1)
                    
            # Determine reason for blocking
            if "web page blocked" in page_source.lower():
                info["reason"] = "Web Application Firewall (WAF) Block"
            elif "access denied" in page_source.lower():
                info["reason"] = "Access Denied"
            elif "forbidden" in page_source.lower():
                info["reason"] = "Forbidden"
            elif "security warning" in page_source.lower():
                info["reason"] = "Security Warning"
                
            return info
            
        except Exception as e:
            print(f"Error extracting blocked page info: {e}")
            return {"blocked": True, "error": str(e)}

    def _get_cookies(self, session_phase: str) -> List[Cookie]:
        """
        Retrieves all cookies from the current browser session and
        validates them using the Pydantic Cookie model.
        """
        raw_cookies = self.driver.get_cookies()
        validated_cookies = []
        for raw_cookie in raw_cookies:
            raw_cookie["session_phase"] = session_phase
            try:
                validated_cookies.append(Cookie(**raw_cookie))
            except Exception as e:
                print(f"Skipping invalid cookie: {raw_cookie} due to error: {e}")
        return validated_cookies

    def _handle_cookie_banner(self, action: CookieBannerAction) -> Optional[str]:
        """
        Attempts to find and interact with a cookie consent banner based on the desired action.

        Args:
            action (CookieBannerAction): The action to take on the banner (ACCEPT_ALL, REJECT_ALL).

        Returns:
            Optional[str]: The action taken ('accepted', 'rejected'), or None if no action was taken.
        """
        # Reset banner found flag for this run
        self._banner_found = False
        # Expanded CSS selectors for cookie banners - more comprehensive coverage
        selectors = [
            # Common English selectors
            "#cookie-banner", ".cookie-notice", ".cookie-consent", "#consent-box",
            "[id*='cookie-consent']", "[class*='cookie-banner']", "[class*='consent']",
            "[id*='gdpr']", "[class*='gdpr']", "[id*='privacy']", "[class*='privacy']",
            
            # Portuguese-specific selectors (common in Portuguese websites)
            "[id*='cookies']", "[class*='cookies']", "[id*='aviso']", "[class*='aviso']",
            "[id*='notificacao']", "[class*='notificacao']", "[id*='permissao']", "[class*='permissao']",
            
            # Generic banner selectors
            "[role='banner']", "[aria-label*='cookie']", "[aria-label*='consent']",
            ".modal", ".popup", ".overlay", ".notification", ".alert",
            
            # Data attributes
            "[data-testid*='cookie']", "[data-testid*='consent']", "[data-testid*='banner']"
        ]
        
        button_keywords = {
            CookieBannerAction.ACCEPT_ALL: [
                "Accept", "Accept All", "Agree", "OK", "Allow", "Enable",
                "Aceitar", "Aceitar Todos", "Aceitar todos", "Concordar", "Permitir", "Ativar",  # Portuguese
                "Sim", "Confirmar", "Prosseguir"  # Portuguese
            ],
            CookieBannerAction.REJECT_ALL: [
                "Reject", "Reject All", "Decline", "Disable", "Block",
                "Negar", "Recusar", "Rejeitar", "Rejeitar todos", "Desativar", "Bloquear",  # Portuguese
                "Não", "Cancelar", "Sair"  # Portuguese
            ]
        }
        
        # Determine keywords based on the desired action
        keywords = button_keywords.get(action, [])
        if not keywords:
            print(f"No keywords defined for action: {action.value}")
            return None

        banner_found = False
        for selector in selectors:
            try:
                banner_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                banner_found = True
                print(f"Found potential cookie banner with selector: {selector}")
                
                for keyword in keywords:
                    # First try direct XPath matches (works well with tests and simple banners)
                    try:
                        button_xpath = f".//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword.lower()}')]"
                        accept_button = banner_element.find_element(By.XPATH, button_xpath)
                        print(f"Found cookie banner with selector '{selector}' and clicking button for '{action.value}' with text '{keyword}' via XPath")
                        accept_button.click()
                        time.sleep(3)
                        self._banner_found = True
                        return action.value
                    except NoSuchElementException:
                        pass

                    try:
                        link_xpath = f".//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword.lower()}')]"
                        accept_link = banner_element.find_element(By.XPATH, link_xpath)
                        print(f"Found cookie banner with selector '{selector}' and clicking link for '{action.value}' with text '{keyword}' via XPath")
                        accept_link.click()
                        time.sleep(3)
                        self._banner_found = True
                        return action.value
                    except NoSuchElementException:
                        pass

                    # Use a recursive approach - search for elements by tag throughout the banner and its children
                    # This handles cases where the selector finds a parent container
                    
                    print(f"  Testing keyword: '{keyword}'")
                    
                    # Try buttons first - search recursively
                    buttons = banner_element.find_elements(By.CSS_SELECTOR, "button, .btn, [role='button']")
                    print(f"    Found {len(buttons)} button(s) in banner element (including children)")
                    for button in buttons:
                        button_text = button.text.strip().lower()
                        print(f"      Button text: '{button_text}'")
                        if keyword.lower() in button_text:
                            print(f"Found cookie banner with selector '{selector}' and clicking button for '{action.value}' with text '{keyword}'")
                            button.click()
                            time.sleep(3) # Wait for the page to update after click
                            self._banner_found = True
                            return action.value
                    
                    # Try links if no button found - search recursively
                    links = banner_element.find_elements(By.CSS_SELECTOR, "a, .btn, [role='link']")
                    print(f"    Found {len(links)} link(s) in banner element (including children)")
                    for link in links:
                        link_text = link.text.strip().lower()
                        print(f"      Link text: '{link_text}'")
                        if keyword.lower() in link_text:
                            print(f"Found cookie banner with selector '{selector}' and clicking link for '{action.value}' with text '{keyword}'")
                            link.click()
                            time.sleep(3) # Wait for the page to update after click
                            self._banner_found = True
                            return action.value
                        
                # Also try to find buttons by common attributes
                try:
                    # Look for buttons with common cookie-related attributes
                    cookie_buttons = banner_element.find_elements(By.CSS_SELECTOR, 
                        "button[data-action*='accept'], button[data-action*='consent'], button[data-testid*='accept']")
                    
                    if cookie_buttons:
                        print(f"Found cookie button by data attributes in selector: {selector}")
                        cookie_buttons[0].click()
                        time.sleep(3)
                        self._banner_found = True
                        return action.value
                except Exception as e:
                    print(f"Error with data attribute button search: {e}")
                    
            except NoSuchElementException:
                continue
        
        if banner_found:
            print(f"Banner found but no suitable button for action: {action.value}.")
        else:
            print(f"No cookie banner found with any selector for action: {action.value}.")
        # Mark that a banner was present even if we could not click
        self._banner_found = banner_found
        return None

    def _find_policy_urls(self) -> tuple[Optional[HttpUrl], Optional[HttpUrl]]:
        """
        Parses the page HTML to find links to privacy and cookie policies.
        """
        privacy_url = None
        cookie_url = None
        
        try:
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            policy_keywords = {
                "privacy": [
                    "privacy", "data policy", "privacy policy", "data protection",
                    "privacidade", "proteção de dados", "política de privacidade"  # Portuguese
                ],
                "cookie": [
                    "cookie", "cookies policy", "cookie policy", "cookie notice",
                    "cookies", "política de cookies", "aviso de cookies", "gestão de cookies"  # Portuguese
                ]
            }
            
            for link in soup.find_all('a', href=True):
                text = link.get_text().strip().lower()
                href = urljoin(self.url, link['href'])
                
                if not privacy_url:
                    if any(keyword in text for keyword in policy_keywords["privacy"]):
                        privacy_url = HttpUrl(href)
                
                if not cookie_url:
                    if any(keyword in text for keyword in policy_keywords["cookie"]):
                        cookie_url = HttpUrl(href)
                
                if privacy_url and cookie_url:
                    break

        except Exception as e:
            print(f"Error parsing HTML for policy links: {e}")
            
        return privacy_url, cookie_url

    def _take_screenshot(self, screenshot_type: str) -> Optional[Screenshot]:
        """
        Takes a full-page screenshot, encodes it in Base64, and returns
        a Pydantic Screenshot object.
        """
        try:
            base64_data = self.driver.get_screenshot_as_base64()
            return Screenshot(screenshot_type=screenshot_type, base64_data=base64_data)
        except Exception as e:
            print(f"Error taking screenshot of type '{screenshot_type}': {e}")
            return None

    def _print_analysis_summary(self, result: WebsiteAnalysisResult):
        """
        Prints a summary of the website analysis results.
        """
        print("\n--- Analysis Summary ---")
        print(f"URL: {result.url}")
        print(f"Analysis Timestamp: {result.analysis_timestamp}")
        print(f"Has Cookie Banner: {result.has_cookie_banner}")
        print(f"Cookie Banner Action: {result.cookie_banner_action if result.cookie_banner_action else 'None'}")
        
        print(f"Privacy Policy URL: {str(result.privacy_policy_url) if result.privacy_policy_url else 'N/A'}")
        print(f"Cookie Policy URL: {str(result.cookie_policy_url) if result.cookie_policy_url else 'N/A'}")
        print(f"Total Cookies Found: {len(result.cookies)}")
        if result.cookies:
            print(f"Cookies:")
            for cookie in result.cookies:
                print(f"  - {cookie.name} (Domain: {cookie.domain}, Path: {cookie.path})")
        else:
            print("No cookies found.")
        
        if result.screenshots:
            print(f"Screenshots Taken: {len(result.screenshots)}")
            for i, screenshot in enumerate(result.screenshots):
                print(f"  Screenshot {i+1} ({screenshot.screenshot_type}):")
                print(f"    Type: {screenshot.screenshot_type}")
                print(f"    Size: {len(screenshot.base64_data) / 1024:.2f} KB")
                print(f"    Base64 Data Length: {len(screenshot.base64_data)}")
        else:
            print("No screenshots were taken.")

        # Note: Blocked page information is logged during analysis but not stored in the result model

    def analyze(self, action: CookieBannerAction = CookieBannerAction.NONE) -> Optional[WebsiteAnalysisResult]:
        """
        Performs the full analysis on the website.

        Args:
            action (CookieBannerAction): The action to take on the cookie banner.

        Returns:
            Optional[WebsiteAnalysisResult]: The final analysis result as a Pydantic
            model, or None if the analysis failed.
        """
        self._setup_driver()
        if not self.driver:
            return None

        screenshots = []
        has_cookie_banner = False
        try:
            print(f"Navigating to {self.url}...")
            
            # Use retry logic with anti-detection measures
            if not self._load_page_with_retry():
                print(f"⚠️  WARNING: Could not load page properly for {self.url}")
                print("   Analysis will continue but results may be limited.")
            
            # Print page title for debugging
            try:
                page_title = self.driver.title
                print(f"Page title: {page_title}")
            except:
                print("Could not get page title")
                
            # Check if page is blocked or didn't load properly
            blocked_info = {}
            if self._is_page_blocked():
                print(f"⚠️  WARNING: Page appears to be blocked by security system for {self.url}")
                blocked_info = self._get_blocked_page_info()
                if blocked_info:
                    print(f"   Blocking Reason: {blocked_info.get('reason', 'Unknown')}")
                    if blocked_info.get('client_ip'):
                        print(f"   Client IP: {blocked_info['client_ip']}")
                    if blocked_info.get('attack_id'):
                        print(f"   Attack ID: {blocked_info['attack_id']}")
                    if blocked_info.get('message_id'):
                        print(f"   Message ID: {blocked_info['message_id']}")
                print("   This may affect the analysis results.")
                
            if not self._is_page_loaded_properly():
                print(f"⚠️  WARNING: Page may not have loaded properly for {self.url}")
                print("   Content appears to be minimal or contains error indicators.")

            initial_cookies = self._get_cookies("initial")
            initial_screenshot = self._take_screenshot("initial")
            if initial_screenshot:
                screenshots.append(initial_screenshot)

            cookie_banner_action = None
            banner_found = False
            if action != CookieBannerAction.NONE:
                cookie_banner_action = self._handle_cookie_banner(action)
                # Set has_cookie_banner based on whether a banner was found, not just if action succeeded
                has_cookie_banner = self._banner_found
            else:
                print("No interaction with the cookie banner was requested.")

            post_interaction_cookies = self._get_cookies("accepted" if has_cookie_banner else "rejected")
            if has_cookie_banner:
                banner_screenshot = self._take_screenshot("banner")
                if banner_screenshot:
                    screenshots.append(banner_screenshot)

            privacy_policy_url, cookie_policy_url = self._find_policy_urls()

            final_cookies = {
                (c.name, c.domain, c.path): c for c in initial_cookies
            }
            final_cookies.update({
                (c.name, c.domain, c.path): c for c in post_interaction_cookies
            })

            result = WebsiteAnalysisResult(
                url=HttpUrl(self.url),
                analysis_timestamp=datetime.now(),
                has_cookie_banner=has_cookie_banner,
                cookie_banner_action=action if has_cookie_banner else CookieBannerAction.NONE,
                privacy_policy_url=privacy_policy_url,
                cookie_policy_url=cookie_policy_url,
                cookies=list(final_cookies.values()),
                screenshots=screenshots
            )
            
            # Print analysis summary
            self._print_analysis_summary(result)
            
            return result

        except (WebDriverException, TimeoutException) as e:
            print(f"WebDriver error during analysis of {self.url}: {e}")
            return None
        finally:
            self._teardown_driver()


if __name__ == "__main__":
    # Example usage for multi-scenario testing
    test_url = "https://www.wikipedia.org/"
    
    # Test "Accept All" scenario
    print("--- Starting 'Accept All' Test ---")
    analyzer_accept = WebsiteAnalyzer(test_url)
    accept_result = analyzer_accept.analyze(action=CookieBannerAction.ACCEPT_ALL)
    if accept_result:
        print(f"Analysis for '{test_url}' with action '{accept_result.cookie_banner_action.value}' completed successfully.")
        print(f"Total Cookies Found: {len(accept_result.cookies)}")

    # Test "Reject All" scenario
    print("\n--- Starting 'Reject All' Test ---")
    analyzer_reject = WebsiteAnalyzer(test_url)
    reject_result = analyzer_reject.analyze(action=CookieBannerAction.REJECT_ALL)
    if reject_result:
        print(f"Analysis for '{test_url}' with action '{reject_result.cookie_banner_action.value}' completed successfully.")
        print(f"Total Cookies Found: {len(reject_result.cookies)}")
