"""
Browser configuration module for enhanced anti-detection and cookie collection.

This module follows the Single Responsibility Principle by handling only
browser setup and configuration concerns.
"""

import random
from typing import Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class BrowserConfigurator:
    """
    Responsible for configuring Chrome browser with anti-detection measures.
    
    Follows Single Responsibility Principle - only handles browser configuration.
    """
    
    @staticmethod
    def create_chrome_options(
        headless: bool = False,
        enable_anti_detection: bool = True,
        language: str = "pt-PT"
    ) -> webdriver.ChromeOptions:
        """
        Creates Chrome options with anti-detection measures.
        
        Args:
            headless: Whether to run in headless mode
            enable_anti_detection: Whether to enable anti-detection measures
            language: Browser language setting
            
        Returns:
            Configured ChromeOptions object
        """
        chrome_options = webdriver.ChromeOptions()
        
        # Basic options
        if headless:
            chrome_options.add_argument("--headless=new")
            
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        if enable_anti_detection:
            BrowserConfigurator._add_anti_detection_options(chrome_options, language)
            
        return chrome_options
    
    @staticmethod
    def _add_anti_detection_options(chrome_options: webdriver.ChromeOptions, language: str):
        """Adds anti-detection specific options."""
        # Remove automation indicators
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Realistic user agent
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
        
        # Language settings
        chrome_options.add_argument(f"--lang={language},en-US,en")
        chrome_options.add_argument(f"--accept-lang={language};q=0.9,en-US;q=0.8,en;q=0.7")
        
        # Disable automation-related features and enhance cookie collection
        automation_flags = [
            "--disable-extensions", "--disable-plugins", "--disable-default-apps",
            "--disable-background-networking", "--disable-sync", "--disable-translate",
            "--disable-popup-blocking",  # Allow popups which might contain cookies
            "--disable-web-security",  # Allow cross-origin requests for better cookie collection
            "--disable-same-site-by-default-cookies",  # Allow more flexible cookie collection
            "--disable-features=SameSiteByDefaultCookies",  # Disable SameSite restrictions
            "--disable-features=VizDisplayCompositor",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows", 
            "--disable-renderer-backgrounding",
            "--no-first-run",
            "--no-default-browser-check"
        ]
        for flag in automation_flags:
            chrome_options.add_argument(flag)
        
        # Enable realistic browser features
        chrome_options.add_argument("--enable-webgl")
        chrome_options.add_argument("--enable-3d-apis")
        
        # Set browser preferences
        prefs = BrowserConfigurator._get_browser_preferences(language)
        chrome_options.add_experimental_option("prefs", prefs)
    
    @staticmethod
    def _get_browser_preferences(language: str) -> Dict[str, Any]:
        """Returns realistic browser preferences."""
        return {
            "profile.default_content_setting_values": {
                "notifications": 2,
                "media_stream": 2,
            },
            "profile.managed_default_content_settings": {
                "images": 1,
            },
            "profile.default_content_settings": {
                "popups": 0,
            },
            "intl.accept_languages": f"{language},en-US,en",
            "intl.charset_default": "UTF-8",
        }
    
    @staticmethod
    def create_driver(chrome_options: webdriver.ChromeOptions) -> webdriver.Chrome:
        """
        Creates and configures Chrome WebDriver.
        
        Args:
            chrome_options: Configured Chrome options
            
        Returns:
            Configured Chrome WebDriver instance
        """
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Set timeouts
        driver.set_page_load_timeout(45)
        driver.implicitly_wait(10)
        
        return driver
    
    @staticmethod
    def apply_anti_detection_scripts(driver: webdriver.Chrome):
        """
        Applies JavaScript-based anti-detection measures.
        
        Args:
            driver: Chrome WebDriver instance
        """
        # Remove webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Override plugins property
        driver.execute_script("""
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
        
        # Override languages property
        driver.execute_script("""
            Object.defineProperty(navigator, 'languages', {
                get: () => ['pt-PT', 'pt', 'en-US', 'en']
            });
        """)
        
        # Set realistic screen properties
        driver.execute_script("""
            Object.defineProperty(screen, 'width', {get: () => 1920});
            Object.defineProperty(screen, 'height', {get: () => 1080});
            Object.defineProperty(screen, 'availWidth', {get: () => 1920});
            Object.defineProperty(screen, 'availHeight', {get: () => 1040});
            Object.defineProperty(screen, 'colorDepth', {get: () => 24});
            Object.defineProperty(screen, 'pixelDepth', {get: () => 24});
        """)


class PageStabilityChecker:
    """
    Handles page loading stability checks and cookie settling time.
    
    Follows Single Responsibility Principle - only handles page stability concerns.
    """
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
    
    def wait_for_stability(self, timeout: int = 10) -> bool:  # Reduced from 15 to 10
        """
        Waits for page to be stable and cookies to be set.
        
        Args:
            timeout: Maximum time to wait for stability
            
        Returns:
            True if page is stable, False if timeout occurred
        """
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            
            # Wait for document ready state
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Reduced wait time for JavaScript execution
            initial_wait = random.uniform(4, 8)  # Reduced from 8-15 to 4-8
            print(f"⏳ Waiting {initial_wait:.1f}s for JavaScript execution...")
            import time
            time.sleep(initial_wait)
            
            # Check if cookies are still being set
            return self._check_cookie_stability()
            
        except Exception as e:
            print(f"⚠️ Page stability check failed: {e}")
            return False
    
    def _check_cookie_stability(self) -> bool:
        """Checks if cookies have stabilized with reduced wait times."""
        import time
        
        initial_count = len(self.driver.get_cookies())
        time.sleep(2)  # Reduced from 3 to 2
        final_count = len(self.driver.get_cookies())
        
        if final_count > initial_count:
            print(f"🍪 Additional cookies detected ({initial_count} -> {final_count}), waiting longer...")
            time.sleep(3)  # Reduced from 5 to 3
            
        return True
    
    def is_page_blocked(self) -> bool:
        """
        Checks if the current page is blocked by security systems.
        
        Returns:
            True if page appears to be blocked
        """
        try:
            page_source = self.driver.page_source.lower()
            page_title = self.driver.title.lower()
            current_url = self.driver.current_url.lower()
            
            blocked_indicators = [
                "web page blocked", "access denied", "blocked by", "security warning",
                "attack id", "client ip", "message id", "page cannot be displayed",
                "contact the administrator", "forbidden", "unauthorized access",
                "security policy", "waf", "web application firewall", "cloudflare",
                "ddos protection", "checking your browser", "just a moment",
                "please wait while we", "security check", "bot protection"
            ]
            
            # Check page content and URL for blocking indicators
            for indicator in blocked_indicators:
                if (indicator in page_source or 
                    indicator in page_title or 
                    indicator in current_url):
                    return True
                    
            return False
            
        except Exception:
            return False
    
    def is_page_loaded_properly(self) -> bool:
        """
        Verifies that the page has loaded with meaningful content.
        
        Returns:
            True if page appears to have loaded properly
        """
        try:
            page_source = self.driver.page_source
            
            # Check minimum content requirements
            if len(page_source) < 1000:
                return False
            
            # Check for body content
            from selenium.webdriver.common.by import By
            from selenium.common.exceptions import NoSuchElementException
            
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                body_text = body.text.strip()
                if len(body_text) < 50:
                    return False
            except NoSuchElementException:
                return False
            
            # Check page title
            title = self.driver.title.strip()
            if not title or len(title) < 3:
                return False
            
            # Check for error patterns
            error_patterns = [
                "error 404", "not found", "page not found", "erro 404",
                "server error", "internal error", "service unavailable",
                "temporarily unavailable", "maintenance mode"
            ]
            
            page_lower = page_source.lower()
            title_lower = title.lower()
            
            for pattern in error_patterns:
                if pattern in page_lower or pattern in title_lower:
                    return False
                    
            return True
            
        except Exception:
            return False