"""
Enhanced cookie collection module.

This module follows the Single Responsibility Principle by handling only
cookie collection and validation concerns.
"""

from typing import List, Dict, Any, Tuple
from urllib.parse import urlparse
from selenium import webdriver
from core.models import Cookie


class CookieCollector:
    """
    Responsible for collecting and validating cookies from web pages.
    
    Follows Single Responsibility Principle - only handles cookie collection.
    """
    
    def __init__(self, driver: webdriver.Chrome, base_url: str):
        self.driver = driver
        self.base_url = base_url
        self._domain = self._extract_domain(base_url)
    
    def collect_cookies(self, session_phase: str) -> List[Cookie]:
        """
        Collects cookies using multiple methods for comprehensive coverage.
        
        Args:
            session_phase: The phase of cookie collection (e.g., 'initial', 'accepted')
            
        Returns:
            List of validated Cookie objects
        """
        selenium_cookies = self._collect_selenium_cookies()
        js_cookies = self._collect_javascript_cookies()
        
        print(f"📊 Selenium: {len(selenium_cookies)} cookies, JavaScript: {len(js_cookies)} additional entries")
        
        # Merge and deduplicate cookies
        merged_cookies = self._merge_cookies(selenium_cookies, js_cookies, session_phase)
        
        # Validate and convert to Cookie objects
        validated_cookies = self._validate_cookies(merged_cookies)
        
        print(f"✅ Total validated cookies: {len(validated_cookies)}")
        return validated_cookies
    
    def _collect_selenium_cookies(self) -> List[Dict[str, Any]]:
        """Collects cookies using Selenium WebDriver."""
        try:
            return self.driver.get_cookies()
        except Exception as e:
            print(f"⚠️ Selenium cookie collection failed: {e}")
            return []
    
    def _collect_javascript_cookies(self) -> List[Dict[str, str]]:
        """Collects cookies using JavaScript document.cookie with enhanced detection."""
        js_script = """
            var cookies = [];
            var allCookies = document.cookie.split(';');
            
            // Collect from document.cookie
            for(var i = 0; i < allCookies.length; i++) {
                var cookie = allCookies[i].trim();
                if(cookie.length > 0) {
                    var parts = cookie.split('=');
                    if(parts.length >= 2) {
                        cookies.push({
                            name: parts[0].trim(),
                            value: parts.slice(1).join('=').trim(),
                            source: 'document.cookie'
                        });
                    }
                }
            }
            
            // Try to collect additional cookies from storage events or globals
            try {
                // Look for any cookie-related global variables
                if(typeof window !== 'undefined') {
                    // Check for common cookie management objects
                    var cookieNames = ['_ga', '_gid', '_fbp', '__utma', '__utmb', '__utmc', '__utmz'];
                    for(var j = 0; j < cookieNames.length; j++) {
                        if(window[cookieNames[j]]) {
                            var found = false;
                            for(var k = 0; k < cookies.length; k++) {
                                if(cookies[k].name === cookieNames[j]) {
                                    found = true;
                                    break;
                                }
                            }
                            if(!found) {
                                cookies.push({
                                    name: cookieNames[j],
                                    value: String(window[cookieNames[j]]),
                                    source: 'window'
                                });
                            }
                        }
                    }
                }
            } catch(e) {
                // Ignore errors in additional collection
            }
            
            return cookies;
        """
        
        try:
            result = self.driver.execute_script(js_script)
            return result if result else []
        except Exception as e:
            print(f"⚠️ JavaScript cookie collection failed: {e}")
            return []
    
    def _merge_cookies(
        self, 
        selenium_cookies: List[Dict[str, Any]], 
        js_cookies: List[Dict[str, str]], 
        session_phase: str
    ) -> List[Dict[str, Any]]:
        """
        Merges cookies from different collection methods, prioritizing Selenium data.
        Enhanced to capture ALL cookies including third-party ones.
        
        Args:
            selenium_cookies: Cookies from Selenium (with full metadata)
            js_cookies: Cookies from JavaScript (name/value only)
            session_phase: Current session phase
            
        Returns:
            Merged list of cookie dictionaries
        """
        cookie_dict = {}
        
        # Add ALL Selenium cookies (including third-party ones)
        for cookie in selenium_cookies:
            key = self._create_cookie_key(cookie)
            cookie_dict[key] = self._normalize_selenium_cookie(cookie, session_phase)
        
        # Add JavaScript cookies that weren't found by Selenium
        selenium_names = {cookie['name'] for cookie in selenium_cookies}
        
        for js_cookie in js_cookies:
            name = js_cookie.get('name', '').strip()
            value = js_cookie.get('value', '').strip()
            
            if name and name not in selenium_names:
                # For JS cookies, use the current domain but also try to detect third-party cookies
                domain = self._detect_cookie_domain(name, value)
                key = (name, domain, '/')
                cookie_dict[key] = self._create_js_cookie(name, value, session_phase, domain)
        
        return list(cookie_dict.values())
    
    def _detect_cookie_domain(self, name: str, value: str) -> str:
        """
        Attempts to detect the actual domain of a cookie based on common patterns.
        This helps identify third-party cookies more accurately.
        """
        # Common third-party cookie patterns
        third_party_patterns = {
            '_ga': '.google.com',
            '_gid': '.google.com', 
            '__utma': '.google.com',
            '__utmb': '.google.com',
            '__utmc': '.google.com',
            '__utmz': '.google.com',
            '_fbp': '.facebook.com',
            '_fbc': '.facebook.com',
            '__Secure-1PSID': '.google.com',
            '__Secure-3PSID': '.google.com',
            'APISID': '.google.com',
            'SAPISID': '.google.com',
            'HSID': '.google.com',
            'SSID': '.google.com',
            'SID': '.google.com',
            'SIDCC': '.google.com',
            'NID': '.google.com',
            'AEC': '.google.com',
            'SOCS': '.google.com',
            '_cfz_google': '.cloudflare.com',
        }
        
        # Check for known patterns
        for pattern, domain in third_party_patterns.items():
            if pattern in name or name.startswith(pattern):
                return domain
                
        # Default to current domain
        return self._domain
    
    def _create_cookie_key(self, cookie: Dict[str, Any]) -> Tuple[str, str, str]:
        """Creates a unique key for cookie deduplication."""
        return (
            cookie.get('name', ''),
            cookie.get('domain', ''),
            cookie.get('path', '/')
        )
    
    def _normalize_selenium_cookie(self, cookie: Dict[str, Any], session_phase: str) -> Dict[str, Any]:
        """Normalizes a Selenium cookie dictionary."""
        return {
            'name': cookie['name'],
            'value': cookie['value'],
            'domain': cookie.get('domain'),
            'path': cookie.get('path', '/'),
            'expires': cookie.get('expiry'),
            'secure': cookie.get('secure', False),
            'http_only': cookie.get('httpOnly', False),  # Note: Selenium uses 'httpOnly'
            'same_site': cookie.get('sameSite'),
            'session_phase': session_phase
        }
    
    def _create_js_cookie(self, name: str, value: str, session_phase: str, domain: str = None) -> Dict[str, Any]:
        """Creates a cookie dictionary from JavaScript collection with domain detection."""
        return {
            'name': name,
            'value': value,
            'domain': domain or self._domain,
            'path': '/',
            'expires': None,
            'secure': False,  # Can't determine from document.cookie
            'http_only': False,  # document.cookie can't access httpOnly cookies
            'same_site': None,
            'session_phase': session_phase
        }
    
    def _validate_cookies(self, cookie_dicts: List[Dict[str, Any]]) -> List[Cookie]:
        """
        Validates cookie dictionaries and converts them to Cookie objects.
        
        Args:
            cookie_dicts: List of cookie dictionaries
            
        Returns:
            List of validated Cookie objects
        """
        validated_cookies = []
        
        for cookie_data in cookie_dicts:
            try:
                # Handle httpOnly field name conversion for Pydantic
                if 'http_only' not in cookie_data and 'httpOnly' in cookie_data:
                    cookie_data['http_only'] = cookie_data.pop('httpOnly')
                
                validated_cookie = Cookie(**cookie_data)
                validated_cookies.append(validated_cookie)
                
            except Exception as e:
                cookie_name = cookie_data.get('name', 'unknown')
                print(f"⚠️ Skipping invalid cookie '{cookie_name}': {e}")
        
        return validated_cookies
    
    def _extract_domain(self, url: str) -> str:
        """Extracts domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return "unknown"


class CookieAnalyzer:
    """
    Analyzes cookie collections and provides insights.
    
    Follows Single Responsibility Principle - only handles cookie analysis.
    """
    
    @staticmethod
    def analyze_cookie_changes(
        initial_cookies: List[Cookie], 
        final_cookies: List[Cookie]
    ) -> Dict[str, Any]:
        """
        Analyzes changes between two cookie collections.
        
        Args:
            initial_cookies: Cookies collected initially
            final_cookies: Cookies collected after interaction
            
        Returns:
            Dictionary containing analysis results
        """
        initial_names = {cookie.name for cookie in initial_cookies}
        final_names = {cookie.name for cookie in final_cookies}
        
        added_cookies = final_names - initial_names
        removed_cookies = initial_names - final_names
        common_cookies = initial_names & final_names
        
        # Analyze value changes for common cookies
        changed_cookies = []
        initial_dict = {cookie.name: cookie.value for cookie in initial_cookies}
        final_dict = {cookie.name: cookie.value for cookie in final_cookies}
        
        for cookie_name in common_cookies:
            if initial_dict[cookie_name] != final_dict[cookie_name]:
                changed_cookies.append(cookie_name)
        
        return {
            'total_initial': len(initial_cookies),
            'total_final': len(final_cookies),
            'added_cookies': list(added_cookies),
            'removed_cookies': list(removed_cookies),
            'changed_cookies': changed_cookies,
            'net_change': len(final_cookies) - len(initial_cookies)
        }
    
    @staticmethod
    def categorize_cookies(cookies: List[Cookie]) -> Dict[str, List[Cookie]]:
        """
        Categorizes cookies by various criteria.
        
        Args:
            cookies: List of cookies to categorize
            
        Returns:
            Dictionary with categorized cookies
        """
        categories = {
            'secure': [],
            'non_secure': [],
            'http_only': [],
            'javascript_accessible': [],
            'session': [],
            'persistent': [],
            'first_party': [],
            'third_party': []
        }
        
        for cookie in cookies:
            # Security categories
            if cookie.secure:
                categories['secure'].append(cookie)
            else:
                categories['non_secure'].append(cookie)
            
            if cookie.http_only:
                categories['http_only'].append(cookie)
            else:
                categories['javascript_accessible'].append(cookie)
            
            # Persistence categories
            if cookie.expires is None:
                categories['session'].append(cookie)
            else:
                categories['persistent'].append(cookie)
            
            # Domain categories (simplified)
            if cookie.domain and ('.' in cookie.domain):
                categories['third_party'].append(cookie)
            else:
                categories['first_party'].append(cookie)
        
        return categories