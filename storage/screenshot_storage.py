import os
import base64
from datetime import datetime
from urllib.parse import urlparse


class ScreenshotStorage:
    """
    Responsible for persisting screenshots to the filesystem in a structured layout.

    - Base directory defaults to 'screenshots' under the project root
    - Files are organized as: <base_dir>/<domain>/<YYYY-MM-DD>/<HHMMSS>_<type>.png
    """

    def __init__(self, base_dir: str = "screenshots") -> None:
        self.base_dir = base_dir

    def save(self, website_url: str, analysis_timestamp: datetime, screenshot_type: str, base64_data: str) -> str:
        """
        Saves the Base64 screenshot to disk and returns the relative filesystem path.

        Args:
            website_url: The analyzed website URL
            analysis_timestamp: When the analysis occurred
            screenshot_type: A short label, e.g. "initial", "banner"
            base64_data: The Base64-encoded PNG data

        Returns:
            The relative path to the saved image file (portable across environments).
        """
        parsed = urlparse(str(website_url))
        domain = self._sanitize(parsed.netloc or parsed.path or "unknown")
        date_part = analysis_timestamp.strftime("%Y-%m-%d")
        time_part = analysis_timestamp.strftime("%H%M%S")
        type_part = self._sanitize(screenshot_type)

        directory = os.path.join(self.base_dir, domain, date_part)
        os.makedirs(directory, exist_ok=True)

        filename = f"{time_part}_{type_part}.png"
        file_path = os.path.join(directory, filename)

        with open(file_path, "wb") as f:
            f.write(base64.b64decode(base64_data))

        # Return relative path so it remains portable
        return file_path

    def _sanitize(self, value: str) -> str:
        """Sanitizes a string for safe filesystem usage."""
        safe = [c if c.isalnum() or c in ("-", "_", ".") else "_" for c in value.strip()]
        # Collapse consecutive underscores
        out = "".join(safe)
        while "__" in out:
            out = out.replace("__", "_")
        return out.strip("._") or "unnamed"


