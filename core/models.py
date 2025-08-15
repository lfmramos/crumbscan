from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl

class CookieBannerAction(str, Enum):
    """
    An Enum to represent the action taken on a cookie banner.
    """
    ACCEPT_ALL = "accepted"
    REJECT_ALL = "rejected"
    NONE = "none"
    
class Screenshot(BaseModel):
    """
    A Pydantic model for a screenshot of a website.
    The image data is stored as a Base64 encoded string.
    """
    screenshot_type: str  # e.g., "initial", "banner"
    base64_data: str

class Cookie(BaseModel):
    """
    A Pydantic model for a single browser cookie.
    """
    name: str
    value: str
    domain: Optional[str] = None
    path: Optional[str] = None
    expires: Optional[float] = None
    secure: bool
    http_only: bool = Field(..., alias="httpOnly")
    session_phase: str  # e.g., "initial", "accepted", "rejected"

    class Config:
        # Allows Pydantic to handle fields with different names, like 'httpOnly'
        populate_by_name = True


class WebsiteAnalysisResult(BaseModel):
    """
    A Pydantic model for the comprehensive analysis of a single website.
    """
    url: HttpUrl
    analysis_timestamp: datetime
    has_cookie_banner: bool
    cookie_banner_action: Optional[str] = None
    privacy_policy_url: Optional[HttpUrl] = None
    cookie_policy_url: Optional[HttpUrl] = None
    cookies: List[Cookie]
    screenshots: List[Screenshot]


if __name__ == "__main__":
    # Example usage and validation check
    # This block will only run if you execute this file directly
    print("Running a quick validation test...")
    example_cookie = {
        "name": "example_cookie",
        "value": "12345",
        "domain": "www.example.com",
        "path": "/",
        "expires": 1735689600.0,
        "secure": True,
        "httpOnly": False,
        "session_phase": "initial",
    }
    
    try:
        cookie_model = Cookie(**example_cookie)
        print("Cookie model created successfully:", cookie_model.model_dump_json(indent=2))
        
        example_result = {
            "url": "https://www.example.com",
            "analysis_timestamp": datetime.now(),
            "has_cookie_banner": True,
            "cookie_banner_action": "accepted",
            "privacy_policy_url": "https://www.example.com/privacy",
            "cookies": [example_cookie],
        }
        
        analysis_result_model = WebsiteAnalysisResult(**example_result)
        print("WebsiteAnalysisResult model created successfully:", analysis_result_model.model_dump_json(indent=2))
    
    except Exception as e:
        print(f"Validation failed: {e}")
