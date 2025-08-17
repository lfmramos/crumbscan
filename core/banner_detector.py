"""
Enhanced cookie banner detection and interaction module.

This module follows the Single Responsibility Principle by handling only
cookie banner detection and interaction concerns.
"""

import time
from typing import List, Optional, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from core.models import CookieBannerAction


class BannerSelector:
    """
    Provides selectors for cookie banner detection.
    
    Follows Single Responsibility Principle - only provides selector data.
    """
    
    @staticmethod
    def get_priority_selectors() -> List[str]:
        """Returns cookie banner selectors in priority order."""
        return [
            # High-priority specific framework selectors
            "#CybotCookiebotDialog", ".CybotCookiebotDialog",
            "#cookieConsent", "#cookie-consent", "#cookies-consent",
            ".cookie-consent", ".cookies-consent", ".cookie-banner",
            "[data-testid*='cookie']", "[data-testid*='consent']",
            
            # Medium-priority generic selectors
            ".modal[id*='cookie']", ".modal[class*='cookie']",
            ".popup[id*='cookie']", ".popup[class*='cookie']",
            ".overlay[id*='cookie']", ".overlay[class*='cookie']",
            
            # Portuguese-specific selectors
            "#avisoPrivacidade", "#avisoCookies", ".aviso-cookies",
            "#consentimentoCookies", ".consentimento-cookies",
            "#politicaPrivacidade", ".politica-privacidade",
            
            # Generic selectors (lower priority)
            ".modal", ".popup", ".overlay", ".notification",
            "[role='dialog']", "[role='banner']", "[role='region']"
        ]


class ButtonKeywords:
    """
    Provides keywords for button detection.
    
    Follows Single Responsibility Principle - only provides keyword data.
    """
    
    @staticmethod
    def get_keywords_for_action(action: CookieBannerAction) -> List[str]:
        """Returns keywords for the given action in priority order."""
        keywords_map = {
            CookieBannerAction.ACCEPT_ALL: [
                # High priority - explicit acceptance
                "accept all", "accept all cookies", "aceitar todos", "aceitar tudo",
                "permitir todos", "concordar", "aceitar", "accept", "allow all",
                "i agree", "concordo", "sim", "ok", "continuar", "prosseguir",
                
                # Medium priority - general acceptance
                "agree", "allow", "enable", "ativar", "permitir", "confirmar"
            ],
            CookieBannerAction.REJECT_ALL: [
                # High priority - explicit rejection
                "reject all", "reject all cookies", "rejeitar todos", "negar todos",
                "recusar todos", "decline all", "block all", "bloquear todos",
                "não aceitar", "recusar", "reject", "decline", "não",
                
                # Medium priority - general rejection
                "block", "disable", "desativar", "cancelar", "sair"
            ]
        }
        
        return keywords_map.get(action, [])


class BannerElementFinder:
    """
    Finds banner elements on the page.
    
    Follows Single Responsibility Principle - only finds banner elements.
    """
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
    
    def find_banner_elements(self) -> List[tuple]:
        """
        Finds all potential banner elements on the page.
        
        Returns:
            List of tuples (priority, selector, element)
        """
        banner_elements = []
        selectors = BannerSelector.get_priority_selectors()
        
        for priority, selector in enumerate(selectors):
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if self._is_element_visible(element):
                        banner_elements.append((priority, selector, element))
                        
            except Exception as e:
                print(f"⚠️ Error with selector '{selector}': {e}")
                continue
        
        return banner_elements
    
    def _is_element_visible(self, element) -> bool:
        """Checks if an element is visible on the page."""
        try:
            return element.is_displayed() and element.size['height'] > 0
        except Exception:
            return True  # Assume visible if check fails


class ButtonInteractor:
    """
    Handles interaction with banner buttons.
    
    Follows Single Responsibility Principle - only handles button interactions.
    """
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
    
    def try_interact_with_banner(
        self, 
        banner_element, 
        action: CookieBannerAction
    ) -> bool:
        """
        Attempts to interact with a banner element for the given action.
        
        Args:
            banner_element: The banner DOM element
            action: The desired action to perform
            
        Returns:
            True if interaction was successful, False otherwise
        """
        keywords = ButtonKeywords.get_keywords_for_action(action)
        
        for keyword in keywords:
            if self._try_click_with_keyword(banner_element, keyword, action.value):
                return True
        
        return False
    
    def _try_click_with_keyword(
        self, 
        banner_element, 
        keyword: str, 
        action_name: str
    ) -> bool:
        """
        Attempts to find and click a button with the given keyword.
        
        Args:
            banner_element: The banner DOM element
            keyword: The keyword to search for
            action_name: Name of the action (for logging)
            
        Returns:
            True if a button was found and clicked
        """
        # Method 1: XPath patterns
        if self._try_xpath_patterns(banner_element, keyword, action_name):
            return True
        
        # Method 2: CSS selector search
        if self._try_css_selectors(banner_element, keyword, action_name):
            return True
        
        return False
    
    def _try_xpath_patterns(self, banner_element, keyword: str, action_name: str) -> bool:
        """Tries various XPath patterns to find buttons."""
        xpath_patterns = [
            f".//button[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ', 'abcdefghijklmnopqrstuvwxyzáàâãéèêíìîóòôõúùûç'), '{keyword.lower()}')]",
            f".//*[@role='button'][contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ', 'abcdefghijklmnopqrstuvwxyzáàâãéèêíìîóòôõúùûç'), '{keyword.lower()}')]",
            f".//a[contains(translate(normalize-space(text()), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ', 'abcdefghijklmnopqrstuvwxyzáàâãéèêíìîóòôõúùûç'), '{keyword.lower()}')]",
            f".//*[contains(translate(normalize-space(@value), 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÀÂÃÉÈÊÍÌÎÓÒÔÕÚÙÛÇ', 'abcdefghijklmnopqrstuvwxyzáàâãéèêíìîóòôõúùûç'), '{keyword.lower()}')]"
        ]
        
        for xpath_pattern in xpath_patterns:
            try:
                button = banner_element.find_element(By.XPATH, xpath_pattern)
                if self._click_element(button, action_name, keyword):
                    return True
            except NoSuchElementException:
                continue
            except Exception as e:
                print(f"⚠️ XPath error: {e}")
                continue
        
        return False
    
    def _try_css_selectors(self, banner_element, keyword: str, action_name: str) -> bool:
        """Tries CSS selectors to find clickable elements."""
        selectors = [
            "button, a, [role='button'], .btn, input[type='button'], input[type='submit']",
            "[onclick], .cookie-accept, .cookie-reject, .cookie-allow, .cookie-deny"
        ]
        
        for selector in selectors:
            try:
                elements = banner_element.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if self._element_matches_keyword(element, keyword):
                        if self._click_element(element, action_name, keyword):
                            return True
            except Exception:
                continue
        
        return False
    
    def _element_matches_keyword(self, element, keyword: str) -> bool:
        """Checks if an element matches the given keyword."""
        try:
            # Collect all text sources
            text_content = (element.get_attribute("textContent") or "").strip().lower()
            title = (element.get_attribute("title") or "").strip().lower()
            aria_label = (element.get_attribute("aria-label") or "").strip().lower()
            data_action = (element.get_attribute("data-action") or "").strip().lower()
            value = (element.get_attribute("value") or "").strip().lower()
            
            all_text = f"{text_content} {title} {aria_label} {data_action} {value}"
            
            return keyword.lower() in all_text and len(text_content) < 100
            
        except Exception:
            return False
    
    def _click_element(self, element, action_name: str, keyword: str) -> bool:
        """Safely clicks an element using JavaScript."""
        try:
            if element.is_displayed() and element.is_enabled():
                text_preview = (element.get_attribute("textContent") or element.text or "")[:50]
                print(f"✅ Clicking element for '{action_name}' with keyword '{keyword}': '{text_preview}...'")
                
                # Use JavaScript click for better reliability
                self.driver.execute_script("arguments[0].click();", element)
                time.sleep(3)  # Wait for page to update
                return True
        except Exception as e:
            print(f"⚠️ Error clicking element: {e}")
        
        return False


class CookieBannerDetector:
    """
    Main cookie banner detection and interaction coordinator.
    
    Follows Single Responsibility Principle and coordinates other classes.
    """
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.element_finder = BannerElementFinder(driver)
        self.button_interactor = ButtonInteractor(driver)
        self._banner_found = False
    
    def detect_and_interact(self, action: CookieBannerAction) -> Optional[str]:
        """
        Detects cookie banner and attempts interaction.
        
        Args:
            action: The desired action to perform
            
        Returns:
            The action performed if successful, None if failed
        """
        self._banner_found = False
        
        if action == CookieBannerAction.NONE:
            print("ℹ️ No banner interaction requested")
            return None
        
        print(f"🔍 Searching for cookie banner for action: {action.value}")
        
        banner_elements = self.element_finder.find_banner_elements()
        
        if not banner_elements:
            print("❌ No cookie banner elements found")
            return None
        
        print(f"🎯 Found {len(banner_elements)} potential banner element(s)")
        
        # Sort by priority (lower number = higher priority)
        banner_elements.sort(key=lambda x: x[0])
        
        for priority, selector, banner_element in banner_elements:
            print(f"  Testing banner with selector: {selector}")
            
            if self.button_interactor.try_interact_with_banner(banner_element, action):
                self._banner_found = True
                print(f"✅ Successfully interacted with banner using action: {action.value}")
                return action.value
        
        # Mark that banners were found even if interaction failed
        self._banner_found = True
        print(f"🍪 Banner(s) found but no suitable button for action: {action.value}")
        
        # Final fallback: try global button search
        return self._fallback_global_search(action)
    
    def _fallback_global_search(self, action: CookieBannerAction) -> Optional[str]:
        """Performs a fallback search across the entire page."""
        print("🔍 Performing fallback global button search...")
        
        try:
            keywords = ButtonKeywords.get_keywords_for_action(action)[:3]  # Top 3 keywords only
            all_buttons = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "button, a, [role='button'], .btn, input[type='button'], input[type='submit']"
            )
            
            print(f"  Checking {len(all_buttons)} clickable elements globally")
            
            for keyword in keywords:
                for button in all_buttons:
                    try:
                        text_content = (button.get_attribute("textContent") or button.text or "").strip().lower()
                        
                        if (keyword.lower() in text_content and 
                            len(text_content) < 100 and 
                            button.is_displayed()):
                            
                            print(f"🎯 Fallback found: '{text_content[:50]}...'")
                            self.driver.execute_script("arguments[0].click();", button)
                            time.sleep(3)
                            return action.value
                            
                    except Exception:
                        continue
                        
        except Exception as e:
            print(f"⚠️ Fallback search failed: {e}")
        
        return None
    
    @property
    def banner_found(self) -> bool:
        """Returns whether a banner was found during the last detection attempt."""
        return self._banner_found