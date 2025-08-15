import sqlite3
import os
from datetime import datetime
from core.models import WebsiteAnalysisResult, Cookie, Screenshot, HttpUrl, CookieBannerAction
from storage.screenshot_storage import ScreenshotStorage
from typing import List, Optional

class DatabaseManager:
    def __init__(self, db_path: str, screenshot_storage: ScreenshotStorage | None = None):
        self.db_path = db_path
        self._ensure_db_directory_exists()
        # Connect to the database and create tables if they don't exist
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        # Pluggable storage for screenshots
        self._screenshot_storage = screenshot_storage or ScreenshotStorage()

    def _ensure_db_directory_exists(self):
        """Ensures the directory for the database file exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

    def _create_tables(self):
        """Creates the necessary database tables with the correct schema."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS websites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                analysis_timestamp TEXT NOT NULL,
                has_cookie_banner INTEGER,
                cookie_banner_action TEXT,
                privacy_policy_url TEXT,
                cookie_policy_url TEXT,
                UNIQUE(url, cookie_banner_action) ON CONFLICT REPLACE
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cookies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                website_id INTEGER,
                name TEXT,
                value TEXT,
                path TEXT,
                domain TEXT,
                secure INTEGER,
                http_only INTEGER,
                same_site TEXT,
                expiry TEXT,
                session_phase TEXT,
                FOREIGN KEY (website_id) REFERENCES websites(id)
            );
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screenshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                website_id INTEGER,
                screenshot_type TEXT NOT NULL,
                base64_data TEXT NOT NULL,
                FOREIGN KEY (website_id) REFERENCES websites(id)
            );
        """)
        
        self.conn.commit()

    def insert_analysis_result(self, result: WebsiteAnalysisResult):
        """Inserts a complete analysis result into the database."""
        try:
            cursor = self.conn.cursor()

            # Insert into websites table
            cursor.execute("""
                INSERT OR REPLACE INTO websites (url, analysis_timestamp, has_cookie_banner, cookie_banner_action, privacy_policy_url, cookie_policy_url)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(result.url),
                result.analysis_timestamp.isoformat(),
                result.has_cookie_banner,
                result.cookie_banner_action,
                str(result.privacy_policy_url) if result.privacy_policy_url else None,
                str(result.cookie_policy_url) if result.cookie_policy_url else None
            ))
            website_id = cursor.lastrowid
            
            # Insert into cookies table
            for cookie in result.cookies:
                cursor.execute("""
                    INSERT INTO cookies (website_id, name, value, domain, path, expiry, secure, http_only, session_phase)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    website_id,
                    cookie.name,
                    cookie.value,
                    cookie.domain,
                    cookie.path,
                    str(cookie.expires) if cookie.expires else None,
                    cookie.secure,
                    cookie.http_only,
                    cookie.session_phase
                ))

            # Save screenshots to disk and record path in DB alongside base64
            for screenshot in result.screenshots:
                # Persist image to filesystem (best-effort; tolerate invalid base64 from mocks/tests)
                try:
                    _ = self._screenshot_storage.save(
                        website_url=str(result.url),
                        analysis_timestamp=result.analysis_timestamp,
                        screenshot_type=screenshot.screenshot_type,
                        base64_data=screenshot.base64_data,
                    )
                except Exception as storage_err:
                    print(f"Warning: failed to save screenshot to disk for {result.url} ({screenshot.screenshot_type}): {storage_err}")

                cursor.execute("""
                    INSERT INTO screenshots (website_id, screenshot_type, base64_data)
                    VALUES (?, ?, ?)
                """, (
                    website_id,
                    screenshot.screenshot_type,
                    screenshot.base64_data
                ))

            self.conn.commit()
            print(f"Successfully inserted analysis results for: {result.url}")

        except sqlite3.Error as e:
            print(f"Database error inserting data for {result.url}: {e}")
            self.conn.rollback()
        
    def get_website_results(self, url: HttpUrl) -> List[WebsiteAnalysisResult]:
        """Retrieves all analysis results for a given URL."""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT * FROM websites WHERE url = ?", (str(url),))
        website_rows = cursor.fetchall()
        
        results = []
        for website_row in website_rows:
            website_id = website_row['id']
            
            cursor.execute("SELECT * FROM cookies WHERE website_id = ?", (website_id,))
            cookie_rows = cursor.fetchall()
            cookies = [Cookie(**dict(row)) for row in cookie_rows]
            
            cursor.execute("SELECT * FROM screenshots WHERE website_id = ?", (website_id,))
            screenshot_rows = cursor.fetchall()
            screenshots = [Screenshot(**dict(row)) for row in screenshot_rows]
            
            result = WebsiteAnalysisResult(
                url=website_row['url'],
                analysis_timestamp=datetime.fromisoformat(website_row['analysis_timestamp']),
                has_cookie_banner=bool(website_row['has_cookie_banner']),
                cookie_banner_action=CookieBannerAction(website_row['cookie_banner_action']) if website_row['cookie_banner_action'] else None,
                privacy_policy_url=website_row['privacy_policy_url'],
                cookie_policy_url=website_row['cookie_policy_url'],
                cookies=cookies,
                screenshots=screenshots
            )
            results.append(result)
            
        return results
