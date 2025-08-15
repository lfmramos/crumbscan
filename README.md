# CrumbScan - Cookie Banner & Privacy Policy Analyzer

A robust web scraping tool designed to analyze websites for cookie banners, privacy policies, and data protection compliance. Built with Python, Selenium, and SQLite, featuring anti-detection measures and comprehensive screenshot storage.

## 🚀 Features

- **Cookie Banner Detection**: Automatically finds and interacts with cookie consent banners
- **Anti-Detection Technology**: Bypasses security systems and WAF blocks
- **Screenshot Storage**: Saves screenshots both to database and organized file system
- **Policy URL Extraction**: Finds privacy and cookie policy links
- **Cookie Analysis**: Collects and analyzes cookies before/after banner interaction
- **Retry Logic**: Smart retry system with random delays for reliability
- **Portuguese Language Support**: Enhanced detection for Portuguese websites
- **Comprehensive Logging**: Detailed analysis reports and warnings

## 📋 Requirements

- Python 3.8+
- Chrome browser
- Internet connection

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd crumbscan
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download ChromeDriver:**
   The application automatically downloads the appropriate ChromeDriver version.

## 🎯 Usage

### Basic Usage

```python
from core.scraper import WebsiteAnalyzer
from core.models import CookieBannerAction

# Create analyzer with anti-detection enabled
analyzer = WebsiteAnalyzer("https://example.com", enable_anti_detection=True)

# Analyze website and accept all cookies
result = analyzer.analyze(action=CookieBannerAction.ACCEPT_ALL)

if result:
    print(f"Cookie banner found: {result.has_cookie_banner}")
    print(f"Cookies found: {len(result.cookies)}")
    print(f"Screenshots taken: {len(result.screenshots)}")
```

### Configuration Options

```python
# Customize retry attempts and anti-detection
analyzer = WebsiteAnalyzer(
    url="https://example.com",
    enable_anti_detection=True,  # Enable/disable stealth measures
    max_retries=5                 # Number of retry attempts
)
```

### Database Storage

```python
from database.db_manager import DatabaseManager

# Store results in database
db_manager = DatabaseManager("results.db")
db_manager.insert_analysis_result(result)
```

## 📁 Project Structure

```
crumbscan/
├── core/                    # Core scraping logic
│   ├── models.py           # Pydantic data models
│   └── scraper.py          # Website analyzer
├── database/               # Database management
│   └── db_manager.py       # SQLite operations
├── storage/                # File storage
│   └── screenshot_storage.py # Screenshot file management
├── data/                   # Configuration data
│   └── websites.txt        # List of websites to analyze
├── tests/                  # Unit tests
├── screenshots/            # Generated screenshots (auto-created)
├── main.py                 # Main application entry point
└── requirements.txt        # Python dependencies
```

## 🔧 Configuration

### Screenshot Storage

Screenshots are automatically saved to:
```
screenshots/
├── domain1.com/
│   └── 2025-08-15/
│       ├── 143022_initial.png
│       └── 143025_banner.png
└── domain2.com/
    └── 2025-08-15/
        └── 143030_initial.png
```

### Anti-Detection Features

- **User-Agent Spoofing**: Realistic browser identification
- **WebDriver Stealth**: Removes automation indicators
- **Random Delays**: Human-like behavior simulation
- **Header Optimization**: Mimics real browser requests

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
python -m unittest discover tests -v

# Run specific test
python -m unittest tests.test_scraper.TestWebsiteAnalyzer.test_analyze_successful -v
```

## 📊 Output

The analyzer provides comprehensive results including:

- **Website Analysis**: URL, timestamp, cookie banner status
- **Cookie Data**: Name, value, domain, security flags, expiration
- **Policy URLs**: Privacy and cookie policy links
- **Screenshots**: Before/after interaction captures
- **Blocking Detection**: WAF and security system warnings

## 🚨 Troubleshooting

### Common Issues

1. **ChromeDriver Errors**: Ensure Chrome browser is installed and up-to-date
2. **WAF Blocks**: Enable anti-detection measures and increase retry attempts
3. **Memory Issues**: Reduce max_retries or disable image loading

### Debug Mode

Enable detailed logging by modifying the scraper configuration:

```python
analyzer = WebsiteAnalyzer(url, enable_anti_detection=True, max_retries=1)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational and research purposes. Always respect website terms of service and robots.txt files. Use responsibly and in compliance with applicable laws and regulations.
