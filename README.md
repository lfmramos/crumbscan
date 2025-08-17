# CrumbScan - Cookie Banner & Privacy Policy Analyzer

A high-performance web scraping tool for analyzing cookie banners, privacy policies, and GDPR compliance. Built with Python and Selenium, optimized for speed and accuracy.

## ✨ Features

- **🍪 Advanced Cookie Analysis** - Detects all cookies including third-party tracking (Google, Facebook, Cloudflare)
- **🎯 Cookie Banner Detection** - Automatically finds and interacts with consent banners
- **⚡ High Performance** - Headless mode with 3x faster analysis than traditional tools
- **🔒 Anti-Detection** - Bypasses security systems with realistic browser simulation
- **� Comprehensive Reports** - Detailed analysis with categorized results
- **🌍 Multi-Language** - Enhanced support for Portuguese websites

## � Quick Start

```bash
# Clone and install
git clone <repository-url>
cd crumbscan
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Run analysis (production mode - fast & headless)
python main_production.py
```

## 📋 Usage Modes

| Script | Browser | Speed | Use Case |
|--------|---------|-------|----------|
| `main_production.py` | Hidden | ⚡⚡⚡ | **Production** (recommended) |
| `main_optimized.py` | Hidden | ⚡⚡ | Development |
| `main_debug.py` | Visible | ⚡ | Troubleshooting |

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

## 🔧 Configuration

### Website List
Add target websites to `data/websites.txt`:
```
https://www.example.com/
https://www.company.pt/
# Comments are supported
```

### Programmatic Usage
```python
from core.scraper import WebsiteAnalyzer
from core.models import CookieBannerAction

# Production configuration (recommended)
analyzer = WebsiteAnalyzer(
    url="https://example.com", 
    headless=True,      # No browser windows
    max_retries=1,      # Fast execution
    language="pt-PT"
)

# Analyze website
result = analyzer.analyze(action=CookieBannerAction.ACCEPT_ALL)
print(f"Cookies found: {len(result.cookies)}")
print(f"Banner detected: {result.has_cookie_banner}")
```

## 📊 Sample Output

```
🚀 Starting HEADLESS production analysis...
==================================================
Analyzing: https://example.com/

✅ Page loaded successfully
🍪 Collecting initial cookies...
📊 Selenium: 2 cookies, JavaScript: 3 additional entries
✅ Total validated cookies: 5

🎯 Attempting cookie banner interaction: accepted
✅ Successfully interacted with banner
📊 Cookie changes: +10 added, 2 modified

============================================================  
📊 ANALYSIS SUMMARY
============================================================
🌐 URL: https://example.com/
🍪 Cookie Banner: ✅ Found
 Total Cookies: 15
   🔒 Secure: 8 | 🚫 HttpOnly: 3 | ⏰ Session: 5 | 💾 Persistent: 10
� Privacy Policy: ✅ Found | 🍪 Cookie Policy: ✅ Found
�📸 Screenshots: 2
============================================================
```

## 🧪 Testing

```bash
# Run all tests
python -m unittest discover tests -v

# Run with coverage
pip install coverage
coverage run -m unittest discover tests
coverage report
```

## 🚨 Troubleshooting

| Problem | Solution |
|---------|----------|
| **Analysis too slow** | Use `main_production.py` (headless mode) |
| **Browser windows visible** | Switch from debug to production mode |
| **Missing cookies** | Expected - fresh session vs your existing cookies |
| **ChromeDriver errors** | Update Chrome browser |
| **Security blocking** | Enable anti-detection (`enable_anti_detection=True`) |

### Debug Mode
```bash
python main_debug.py  # Interactive debugging with visible browser
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for changes
4. Run test suite: `python -m unittest discover tests -v`
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## ⚠️ Disclaimer

For educational and research purposes only. Respect website terms of service and privacy laws (GDPR, CCPA). Use responsibly.

---

**Quick Commands:**
```bash
# Production analysis (fast, headless)
python main_production.py

# Debug with visible browser  
python main_debug.py

# Run tests
python -m unittest discover tests -v
```
