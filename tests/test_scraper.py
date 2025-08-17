"""
Enhanced test suite for the improved website analyzer components.

This test suite follows testing best practices and covers the new modular components.
"""

import unittest
from unittest.mock import MagicMock, patch, Mock
from datetime import datetime

# Import the components we're testing
from core.browser_config import BrowserConfigurator, PageStabilityChecker
from core.cookie_collector import CookieCollector, CookieAnalyzer
from core.banner_detector import CookieBannerDetector, BannerSelector, ButtonKeywords
from core.models import Cookie, CookieBannerAction, WebsiteAnalysisResult


class TestBrowserConfigurator(unittest.TestCase):
    """Tests for the BrowserConfigurator class."""
    
    def test_create_chrome_options_basic(self):
        """Test basic Chrome options creation."""
        options = BrowserConfigurator.create_chrome_options()
        
        # Check that we get a ChromeOptions object
        self.assertIsNotNone(options)
        
        # Verify basic arguments are present
        arguments = options.arguments
        self.assertIn("--no-sandbox", arguments)
        self.assertIn("--disable-dev-shm-usage", arguments)
    
    def test_create_chrome_options_headless(self):
        """Test headless mode configuration."""
        options = BrowserConfigurator.create_chrome_options(headless=True)
        
        arguments = options.arguments
        self.assertIn("--headless=new", arguments)
    
    def test_create_chrome_options_anti_detection(self):
        """Test anti-detection options."""
        options = BrowserConfigurator.create_chrome_options(enable_anti_detection=True)
        
        arguments = options.arguments
        self.assertIn("--disable-blink-features=AutomationControlled", arguments)
        
        # Check experimental options
        exp_options = options.experimental_options
        self.assertIn("excludeSwitches", exp_options)
        self.assertIn("enable-automation", exp_options["excludeSwitches"])
    
    def test_browser_preferences(self):
        """Test browser preferences configuration."""
        prefs = BrowserConfigurator._get_browser_preferences("pt-PT")
        
        self.assertIn("profile.default_content_setting_values", prefs)
        self.assertIn("intl.accept_languages", prefs)
        self.assertEqual(prefs["intl.accept_languages"], "pt-PT,en-US,en")
    
    @patch('core.browser_config.ChromeDriverManager')
    @patch('core.browser_config.webdriver.Chrome')
    def test_create_driver(self, mock_chrome, mock_cdm):
        """Test driver creation with mocked dependencies."""
        mock_cdm.return_value.install.return_value = "/path/to/chromedriver"
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        options = BrowserConfigurator.create_chrome_options()
        driver = BrowserConfigurator.create_driver(options)
        
        # Verify driver was created and configured
        mock_chrome.assert_called_once()
        mock_driver.set_page_load_timeout.assert_called_with(45)
        mock_driver.implicitly_wait.assert_called_with(10)
    
    def test_apply_anti_detection_scripts(self):
        """Test anti-detection script application."""
        mock_driver = Mock()
        
        BrowserConfigurator.apply_anti_detection_scripts(mock_driver)
        
        # Verify JavaScript was executed
        self.assertTrue(mock_driver.execute_script.called)
        # Check that multiple scripts were executed
        self.assertGreater(mock_driver.execute_script.call_count, 1)


class TestPageStabilityChecker(unittest.TestCase):
    """Tests for the PageStabilityChecker class."""
    
    def setUp(self):
        self.mock_driver = Mock()
        self.checker = PageStabilityChecker(self.mock_driver)
    
    def test_is_page_blocked_true(self):
        """Test blocked page detection."""
        self.mock_driver.page_source = "Web page blocked by security"
        self.mock_driver.title = "Blocked"
        self.mock_driver.current_url = "https://example.com"
        
        result = self.checker.is_page_blocked()
        self.assertTrue(result)
    
    def test_is_page_blocked_false(self):
        """Test normal page detection."""
        self.mock_driver.page_source = "Welcome to our website"
        self.mock_driver.title = "Home Page"
        self.mock_driver.current_url = "https://example.com"
        
        result = self.checker.is_page_blocked()
        self.assertFalse(result)
    
    def test_is_page_loaded_properly_true(self):
        """Test proper page loading detection."""
        self.mock_driver.page_source = "A" * 2000  # Long enough content
        self.mock_driver.title = "Valid Page Title"
        
        # Mock body element
        mock_body = Mock()
        mock_body.text = "Some meaningful content here with enough text to meet the minimum requirement"  # 78 chars > 50
        self.mock_driver.find_element.return_value = mock_body
        
        result = self.checker.is_page_loaded_properly()
        self.assertTrue(result)
    
    def test_is_page_loaded_properly_false_short_content(self):
        """Test detection of pages with insufficient content."""
        self.mock_driver.page_source = "Short"  # Too short
        self.mock_driver.title = "Title"
        
        result = self.checker.is_page_loaded_properly()
        self.assertFalse(result)


class TestCookieCollector(unittest.TestCase):
    """Tests for the CookieCollector class."""
    
    def setUp(self):
        self.mock_driver = Mock()
        self.collector = CookieCollector(self.mock_driver, "https://example.com")
    
    def test_collect_selenium_cookies(self):
        """Test Selenium cookie collection."""
        mock_cookies = [
            {
                'name': 'test_cookie',
                'value': 'test_value',
                'domain': 'example.com',
                'path': '/',
                'secure': True,
                'httpOnly': False
            }
        ]
        self.mock_driver.get_cookies.return_value = mock_cookies
        
        result = self.collector._collect_selenium_cookies()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'test_cookie')
    
    def test_collect_javascript_cookies(self):
        """Test JavaScript cookie collection."""
        js_cookies = [{'name': 'js_cookie', 'value': 'js_value'}]
        self.mock_driver.execute_script.return_value = js_cookies
        
        result = self.collector._collect_javascript_cookies()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'js_cookie')
    
    def test_validate_cookies(self):
        """Test cookie validation."""
        cookie_dicts = [
            {
                'name': 'valid_cookie',
                'value': 'value',
                'domain': 'example.com',
                'path': '/',
                'secure': True,
                'http_only': False,
                'session_phase': 'initial'
            },
            {
                'name': 'invalid_cookie',
                # Missing required fields to cause validation error
                'session_phase': 'initial'
            }
        ]
        
        result = self.collector._validate_cookies(cookie_dicts)
        
        # Should only have the valid cookie
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Cookie)
        self.assertEqual(result[0].name, 'valid_cookie')
    
    def test_merge_cookies(self):
        """Test cookie merging logic."""
        selenium_cookies = [
            {
                'name': 'selenium_cookie',
                'value': 'sel_value',
                'domain': 'example.com',
                'secure': True,
                'httpOnly': False
            }
        ]
        
        js_cookies = [
            {'name': 'js_only_cookie', 'value': 'js_value'},
            {'name': 'selenium_cookie', 'value': 'duplicate'}  # Should be ignored
        ]
        
        result = self.collector._merge_cookies(selenium_cookies, js_cookies, 'test_phase')
        
        # Should have 2 cookies: one from Selenium and one JS-only
        self.assertEqual(len(result), 2)
        
        cookie_names = [cookie['name'] for cookie in result]
        self.assertIn('selenium_cookie', cookie_names)
        self.assertIn('js_only_cookie', cookie_names)


class TestCookieAnalyzer(unittest.TestCase):
    """Tests for the CookieAnalyzer class."""
    
    def setUp(self):
        self.initial_cookies = [
            Cookie(name='cookie1', value='value1', secure=True, http_only=False, session_phase='initial'),
            Cookie(name='cookie2', value='value2', secure=False, http_only=True, session_phase='initial')
        ]
        
        self.final_cookies = [
            Cookie(name='cookie1', value='new_value1', secure=True, http_only=False, session_phase='final'),
            Cookie(name='cookie3', value='value3', secure=True, http_only=False, session_phase='final')
        ]
    
    def test_analyze_cookie_changes(self):
        """Test cookie change analysis."""
        result = CookieAnalyzer.analyze_cookie_changes(self.initial_cookies, self.final_cookies)
        
        self.assertEqual(result['total_initial'], 2)
        self.assertEqual(result['total_final'], 2)
        self.assertEqual(result['added_cookies'], ['cookie3'])
        self.assertEqual(result['removed_cookies'], ['cookie2'])
        self.assertEqual(result['changed_cookies'], ['cookie1'])
        self.assertEqual(result['net_change'], 0)
    
    def test_categorize_cookies(self):
        """Test cookie categorization."""
        cookies = [
            Cookie(name='secure_cookie', value='val', secure=True, http_only=False, session_phase='test'),
            Cookie(name='insecure_cookie', value='val', secure=False, http_only=True, session_phase='test'),
            Cookie(name='session_cookie', value='val', secure=False, http_only=False, 
                  expires=None, session_phase='test'),
            Cookie(name='persistent_cookie', value='val', secure=True, http_only=False, 
                  expires=1735689600.0, session_phase='test')
        ]
        
        result = CookieAnalyzer.categorize_cookies(cookies)
        
        self.assertEqual(len(result['secure']), 2)
        self.assertEqual(len(result['non_secure']), 2)
        self.assertEqual(len(result['http_only']), 1)
        self.assertEqual(len(result['javascript_accessible']), 3)
        self.assertEqual(len(result['session']), 3)  # Fixed: 3 cookies have expires=None
        self.assertEqual(len(result['persistent']), 1)


class TestBannerSelector(unittest.TestCase):
    """Tests for the BannerSelector class."""
    
    def test_get_priority_selectors(self):
        """Test that priority selectors are returned."""
        selectors = BannerSelector.get_priority_selectors()
        
        self.assertIsInstance(selectors, list)
        self.assertGreater(len(selectors), 0)
        
        # Check for some expected selectors
        self.assertIn("#CybotCookiebotDialog", selectors)
        self.assertIn("#cookieConsent", selectors)
        self.assertIn(".cookie-consent", selectors)


class TestButtonKeywords(unittest.TestCase):
    """Tests for the ButtonKeywords class."""
    
    def test_get_keywords_for_accept_all(self):
        """Test keywords for ACCEPT_ALL action."""
        keywords = ButtonKeywords.get_keywords_for_action(CookieBannerAction.ACCEPT_ALL)
        
        self.assertIsInstance(keywords, list)
        self.assertGreater(len(keywords), 0)
        
        # Check for expected keywords
        self.assertIn("accept all", keywords)
        self.assertIn("aceitar todos", keywords)
        self.assertIn("accept", keywords)
    
    def test_get_keywords_for_reject_all(self):
        """Test keywords for REJECT_ALL action."""
        keywords = ButtonKeywords.get_keywords_for_action(CookieBannerAction.REJECT_ALL)
        
        self.assertIsInstance(keywords, list)
        self.assertGreater(len(keywords), 0)
        
        # Check for expected keywords
        self.assertIn("reject all", keywords)
        self.assertIn("rejeitar todos", keywords)
        self.assertIn("reject", keywords)
    
    def test_get_keywords_for_none_action(self):
        """Test keywords for NONE action."""
        keywords = ButtonKeywords.get_keywords_for_action(CookieBannerAction.NONE)
        
        self.assertEqual(keywords, [])


class TestBannerElementFinder(unittest.TestCase):
    """Tests for the BannerElementFinder class."""
    
    def setUp(self):
        self.mock_driver = Mock()
        from core.banner_detector import BannerElementFinder
        self.finder = BannerElementFinder(self.mock_driver)
    
    def test_find_banner_elements_found(self):
        """Test finding banner elements."""
        # Mock elements
        mock_element1 = Mock()
        mock_element1.is_displayed.return_value = True
        mock_element1.size = {'height': 100}
        
        mock_element2 = Mock()
        mock_element2.is_displayed.return_value = False
        mock_element2.size = {'height': 0}
        
        # Mock driver to return elements for first selector, none for others
        def mock_find_elements(by, selector):
            if selector == "#CybotCookiebotDialog":
                return [mock_element1, mock_element2]
            return []
        
        self.mock_driver.find_elements.side_effect = mock_find_elements
        
        result = self.finder.find_banner_elements()
        
        # Should find only the visible element
        self.assertEqual(len(result), 1)
        priority, selector, element = result[0]
        self.assertEqual(priority, 0)  # First selector has priority 0
        self.assertEqual(selector, "#CybotCookiebotDialog")
        self.assertEqual(element, mock_element1)
    
    def test_find_banner_elements_none_found(self):
        """Test when no banner elements are found."""
        self.mock_driver.find_elements.return_value = []
        
        result = self.finder.find_banner_elements()
        self.assertEqual(len(result), 0)


class TestButtonInteractor(unittest.TestCase):
    """Tests for the ButtonInteractor class."""
    
    def setUp(self):
        self.mock_driver = Mock()
        from core.banner_detector import ButtonInteractor
        self.interactor = ButtonInteractor(self.mock_driver)
    
    def test_element_matches_keyword_true(self):
        """Test element matching with keyword."""
        mock_element = Mock()
        mock_element.get_attribute.side_effect = lambda attr: {
            'textContent': 'Accept All Cookies',
            'title': '',
            'aria-label': '',
            'data-action': '',
            'value': ''
        }.get(attr, '')
        
        result = self.interactor._element_matches_keyword(mock_element, "accept all")
        self.assertTrue(result)
    
    def test_element_matches_keyword_false(self):
        """Test element not matching with keyword."""
        mock_element = Mock()
        mock_element.get_attribute.side_effect = lambda attr: {
            'textContent': 'Close',
            'title': '',
            'aria-label': '',
            'data-action': '',
            'value': ''
        }.get(attr, '')
        
        result = self.interactor._element_matches_keyword(mock_element, "accept all")
        self.assertFalse(result)
    
    def test_click_element_success(self):
        """Test successful element clicking."""
        mock_element = Mock()
        mock_element.is_displayed.return_value = True
        mock_element.is_enabled.return_value = True
        mock_element.get_attribute.return_value = "Accept All"
        mock_element.text = "Accept All"
        
        result = self.interactor._click_element(mock_element, "accept", "accept all")
        
        self.assertTrue(result)
        self.mock_driver.execute_script.assert_called_with("arguments[0].click();", mock_element)
    
    def test_click_element_not_displayed(self):
        """Test clicking element that's not displayed."""
        mock_element = Mock()
        mock_element.is_displayed.return_value = False
        
        result = self.interactor._click_element(mock_element, "accept", "accept all")
        self.assertFalse(result)


class TestCookieBannerDetector(unittest.TestCase):
    """Tests for the CookieBannerDetector class."""
    
    def setUp(self):
        self.mock_driver = Mock()
        self.detector = CookieBannerDetector(self.mock_driver)
    
    def test_detect_and_interact_none_action(self):
        """Test detection with NONE action."""
        result = self.detector.detect_and_interact(CookieBannerAction.NONE)
        self.assertIsNone(result)
    
    @patch('core.banner_detector.BannerElementFinder')
    @patch('core.banner_detector.ButtonInteractor')
    def test_detect_and_interact_success(self, mock_interactor_class, mock_finder_class):
        """Test successful banner detection and interaction."""
        # Setup mocks
        mock_finder = Mock()
        mock_interactor = Mock()
        mock_finder_class.return_value = mock_finder
        mock_interactor_class.return_value = mock_interactor
        
        mock_element = Mock()
        mock_finder.find_banner_elements.return_value = [(0, "#test-selector", mock_element)]
        mock_interactor.try_interact_with_banner.return_value = True
        
        # Create detector with mocked dependencies
        detector = CookieBannerDetector(self.mock_driver)
        detector.element_finder = mock_finder
        detector.button_interactor = mock_interactor
        
        result = detector.detect_and_interact(CookieBannerAction.ACCEPT_ALL)
        
        self.assertEqual(result, "accepted")
        self.assertTrue(detector.banner_found)
        mock_interactor.try_interact_with_banner.assert_called_once_with(mock_element, CookieBannerAction.ACCEPT_ALL)
    
    @patch('core.banner_detector.BannerElementFinder')
    def test_detect_and_interact_no_banners(self, mock_finder_class):
        """Test detection when no banners are found."""
        mock_finder = Mock()
        mock_finder_class.return_value = mock_finder
        mock_finder.find_banner_elements.return_value = []
        
        detector = CookieBannerDetector(self.mock_driver)
        detector.element_finder = mock_finder
        
        result = detector.detect_and_interact(CookieBannerAction.ACCEPT_ALL)
        
        self.assertIsNone(result)
        self.assertFalse(detector.banner_found)


class TestWebsiteAnalyzerIntegration(unittest.TestCase):
    """Integration tests for the enhanced WebsiteAnalyzer."""
    
    @patch('core.scraper.BrowserConfigurator')
    @patch('core.scraper.PageStabilityChecker')
    @patch('core.scraper.CookieCollector')
    @patch('core.scraper.CookieBannerDetector')
    def test_analyze_successful_flow(self, mock_detector_class, mock_collector_class, 
                                   mock_checker_class, mock_config_class):
        """Test successful analysis flow with mocked components."""
        # Import here to avoid circular imports during test discovery
        from core.scraper import WebsiteAnalyzer
        
        # Setup mocks
        mock_driver = Mock()
        mock_config_class.create_chrome_options.return_value = Mock()
        mock_config_class.create_driver.return_value = mock_driver
        
        mock_checker = Mock()
        mock_checker_class.return_value = mock_checker
        mock_checker.wait_for_stability.return_value = True
        mock_checker.is_page_loaded_properly.return_value = True
        mock_checker.is_page_blocked.return_value = False
        
        mock_collector = Mock()
        mock_collector_class.return_value = mock_collector
        mock_cookies = [Cookie(name='test', value='val', secure=True, http_only=False, session_phase='initial')]
        mock_collector.collect_cookies.return_value = mock_cookies
        
        mock_detector = Mock()
        mock_detector_class.return_value = mock_detector
        mock_detector.detect_and_interact.return_value = "accepted"
        mock_detector.banner_found = True
        
        # Setup driver mocks
        mock_driver.title = "Test Page"
        mock_driver.current_url = "https://example.com"
        mock_driver.get_screenshot_as_base64.return_value = "mock_base64"
        mock_driver.page_source = "<html><body><a href='/privacy'>Privacy</a></body></html>"
        
        # Test the analyzer
        analyzer = WebsiteAnalyzer("https://example.com")
        result = analyzer.analyze(CookieBannerAction.ACCEPT_ALL)
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertIsInstance(result, WebsiteAnalysisResult)
        self.assertTrue(result.has_cookie_banner)
        self.assertEqual(result.cookie_banner_action, "accepted")
        self.assertEqual(len(result.cookies), 1)
        
        # Verify mocks were called
        mock_config_class.create_chrome_options.assert_called_once()
        mock_config_class.create_driver.assert_called_once()
        mock_checker.wait_for_stability.assert_called_once()
        mock_collector.collect_cookies.assert_called()
        mock_detector.detect_and_interact.assert_called_once_with(CookieBannerAction.ACCEPT_ALL)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)