# CrumbScan - Cookie Banner & Privacy Policy Analyzer

A high-performance web scraping tool designed to analyze websites for cookie banners, privacy policies, and data protection compliance. Built with Python, Selenium, and SQLite, featuring optimized performance, anti-detection measures, and comprehensive cookie analysis.

## ✨ Key Features

- **🍪 Advanced Cookie Collection**: Enhanced detection of all cookies including third-party tracking cookies (Google Analytics, Facebook, Cloudflare)
- **🎯 Cookie Banner Detection**: Automatically finds and interacts with cookie consent banners with Portuguese language support
- **⚡ High Performance**: Optimized browser session reuse and headless mode for 3-5x faster analysis
- **🔒 Anti-Detection Technology**: Bypasses security systems and WAF blocks with realistic browser simulation
- **📸 Screenshot Storage**: Saves screenshots both to database and organized file system
- **📋 Policy URL Extraction**: Finds privacy and cookie policy links automatically
- **📊 Comprehensive Analysis**: Detailed cookie categorization (secure, session, persistent, httpOnly)
- **🔄 Smart Retry Logic**: Intelligent retry system with exponential backoff for reliability
- **🌍 Multi-Language Support**: Enhanced detection for Portuguese websites (pt-PT)
- **📝 Detailed Logging**: Comprehensive analysis reports with emoji indicators

## 🚀 Performance Optimizations

- **Headless Mode**: No visible browser windows for production use (3x faster)
- **Session Reuse**: Single browser instance per website instead of per scenario
- **Reduced Wait Times**: Optimized JavaScript execution waits (4-8s vs 8-15s)
- **Smart Retries**: Fewer retry attempts with faster backoff (2 attempts vs 3)
- **Enhanced Cookie Detection**: Better third-party cookie collection with domain recognition

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

### Quick Start (Production Mode)

For production use with maximum performance and no visible browser windows:

```bash
# Run production analysis (headless, optimized)
python main_production.py
```

### Available Execution Modes

| Script | Browser Windows | Speed | Use Case |
|--------|----------------|--------|----------|
| `main_production.py` | ❌ Headless | ⚡⚡⚡ Fastest | Production analysis |
| `main_optimized.py` | ❌ Headless | ⚡⚡ Fast | Daily development |
| `main_super_optimized.py` | ❌ Headless | ⚡⚡⚡ Fastest | Speed testing |
| `main_debug.py` | ✅ Visible | 🐌 Slowest | Troubleshooting only |
| `main.py` | ✅ Visible | 🐌 Slow | Legacy/manual testing |

### Programmatic Usage

```python
from core.scraper import WebsiteAnalyzer
from core.models import CookieBannerAction

# Production configuration (headless, fast)
analyzer = WebsiteAnalyzer(
    url="https://example.com", 
    enable_anti_detection=True,
    max_retries=1,  # Fast retries
    headless=True,  # No browser windows
    language="pt-PT"
)

# Setup browser once for multiple scenarios
analyzer._setup_driver()

# Analyze multiple scenarios efficiently
actions = [CookieBannerAction.ACCEPT_ALL, CookieBannerAction.REJECT_ALL, CookieBannerAction.NONE]
for action in actions:
    result = analyzer._analyze_with_existing_driver(action=action)
    print(f"Action: {action.value}, Cookies: {len(result.cookies)}")

# Cleanup
analyzer._teardown_driver()
```

### Single Analysis

```python
# Traditional single analysis (creates/destroys browser for each run)
analyzer = WebsiteAnalyzer("https://example.com")
result = analyzer.analyze(action=CookieBannerAction.ACCEPT_ALL)

if result:
    print(f"Cookie banner found: {result.has_cookie_banner}")
    print(f"Total cookies: {len(result.cookies)}")
    print(f"Secure cookies: {len([c for c in result.cookies if c.secure])}")
    print(f"Screenshots: {len(result.screenshots)}")
```

### Performance Configuration

```python
# Maximum performance (headless, minimal retries)
analyzer = WebsiteAnalyzer(
    url="https://example.com",
    enable_anti_detection=True,   # Better success rate
    max_retries=1,               # Fast failures
    headless=True,               # No GUI overhead
    language="pt-PT"             # Portuguese websites
)

# Debug configuration (visible browser, more retries)
analyzer = WebsiteAnalyzer(
    url="https://example.com",
    enable_anti_detection=True,
    max_retries=3,               # More attempts
    headless=False,              # Visible for debugging
    language="pt-PT"
)
```

### Cookie Analysis Features

```python
# Enhanced cookie collection with third-party detection
result = analyzer.analyze(action=CookieBannerAction.ACCEPT_ALL)

# Analyze collected cookies
from core.cookie_collector import CookieAnalyzer
categories = CookieAnalyzer.categorize_cookies(result.cookies)

print(f"Secure cookies: {len(categories['secure'])}")
print(f"Session cookies: {len(categories['session'])}")  
print(f"Persistent cookies: {len(categories['persistent'])}")
print(f"HttpOnly cookies: {len(categories['http_only'])}")

# Cookie change analysis
changes = CookieAnalyzer.analyze_cookie_changes(initial_cookies, final_cookies)
print(f"Added: {changes['added_cookies']}")
print(f"Modified: {changes['changed_cookies']}")
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
├── core/                           # Enhanced modular core components
│   ├── banner_detector.py        # Cookie banner detection & interaction
│   ├── browser_config.py         # Optimized browser configuration
│   ├── cookie_collector.py       # Advanced cookie collection & analysis
│   ├── models.py                 # Pydantic data models
│   └── scraper.py                # Main website analyzer with optimizations
├── database/                      # Database management
│   └── db_manager.py             # SQLite operations & storage
├── storage/                       # File storage management
│   └── screenshot_storage.py     # Screenshot file organization
├── tests/                         # Comprehensive test suite (30+ tests)
│   ├── test_banner_detector.py   # Banner detection tests
│   ├── test_browser_config.py    # Browser configuration tests  
│   ├── test_cookie_collector.py  # Cookie collection tests
│   ├── test_db_manager.py        # Database tests
│   └── test_scraper.py           # Main analyzer tests
├── data/                          # Configuration data
│   └── websites.txt              # Target websites list
├── screenshots/                   # Auto-generated screenshots
│   ├── domain1.com/
│   │   └── 2025-08-17/
│   │       ├── 151548_initial.png
│   │       └── 151548_banner.png
│   └── domain2.com/
├── main_production.py             # 🚀 Production (headless, fastest)
├── main_optimized.py             # ⚡ Optimized (headless, session reuse)
├── main_super_optimized.py       # 🏃 Super optimized (minimal retries)
├── main_debug.py                 # 🐛 Debug (visible browser)
├── main.py                       # 📜 Legacy (original version)
├── requirements.txt              # Dependencies
└── data_protection_results.db    # SQLite database (auto-created)
```

## 🔧 Configuration

### Website List Configuration

Add target websites to `data/websites.txt`:
```
https://www.example.com/
https://www.company.pt/
# Comments are supported
https://www.municipality.pt/
```

### Performance Tuning

Choose the right execution mode for your needs:

- **Production**: `main_production.py` - Headless, single retries, maximum speed
- **Development**: `main_optimized.py` - Balanced performance and reliability  
- **Testing**: `main_super_optimized.py` - Fastest possible, minimal error handling
- **Debugging**: `main_debug.py` - Visible browser, interactive prompts

### Browser Configuration

Advanced browser settings are automatically optimized:

```python
# Automatic optimizations include:
- Headless mode for production
- Anti-detection measures (user-agent spoofing, WebDriver stealth)
- Cookie collection enhancements (SameSite bypass, cross-origin)
- Performance improvements (image blocking, popup allowing)
- Portuguese language preference
```

## 🧪 Testing

The project includes a comprehensive test suite with 30+ tests covering all components:

```bash
# Run all tests
python -m unittest discover tests -v

# Run with coverage analysis
pip install coverage
coverage run -m unittest discover tests
coverage report
coverage html  # Generates HTML report

# Run specific component tests
python -m unittest tests.test_scraper -v
python -m unittest tests.test_cookie_collector -v
python -m unittest tests.test_banner_detector -v

# Test specific functionality
python -m unittest tests.test_scraper.TestCookieAnalyzer.test_categorize_cookies -v
```

### Test Coverage

- ✅ **WebsiteAnalyzer**: Main scraping logic and optimization features
- ✅ **CookieCollector**: Enhanced cookie collection and third-party detection  
- ✅ **CookieBannerDetector**: Banner finding and interaction
- ✅ **BrowserConfigurator**: Anti-detection and performance optimization
- ✅ **DatabaseManager**: Data persistence and retrieval
- ✅ **Models**: Pydantic validation and data structures

## 📊 Output & Analysis

### Sample Analysis Output

```
🚀 Starting HEADLESS production analysis...
==================================================
Analyzing: https://example.com/

--- Scenario 1/3: accepted ---
🌐 Loading page (attempt 1)...
⏳ Waiting 5.2s for JavaScript execution...  
✅ Page loaded successfully
📄 Page title: Example Domain
🌐 Current URL: https://example.com/

🍪 Collecting initial cookies...
📊 Selenium: 2 cookies, JavaScript: 3 additional entries
✅ Total validated cookies: 5

🎯 Attempting cookie banner interaction: accepted
🔍 Searching for cookie banner for action: accepted  
🎯 Found 3 potential banner element(s)
✅ Successfully interacted with banner using action: accepted

🍪 Collecting post-interaction cookies...
📊 Selenium: 8 cookies, JavaScript: 12 additional entries
✅ Total validated cookies: 15
📊 Cookie changes: +10 added, 2 modified

============================================================  
📊 ANALYSIS SUMMARY
============================================================
🌐 URL: https://example.com/
📅 Timestamp: 2025-08-17 16:45:22
🍪 Cookie Banner: ✅ Found
🎯 Action Taken: accepted
📋 Privacy Policy: ✅ Found  
🍪 Cookie Policy: ✅ Found
🍪 Total Cookies: 15
   🔒 Secure: 8
   🚫 HttpOnly: 3  
   ⏰ Session: 5
   💾 Persistent: 10
📸 Screenshots: 2
============================================================
```

### Enhanced Cookie Analysis

The analyzer now provides detailed cookie categorization:

- **Third-party Detection**: Automatically identifies Google Analytics, Facebook, Cloudflare cookies
- **Security Analysis**: Flags secure, HttpOnly, and SameSite cookie attributes
- **Persistence Tracking**: Distinguishes between session and persistent cookies
- **Domain Classification**: Identifies first-party vs third-party cookie sources
- **Change Tracking**: Shows exactly which cookies were added/modified after banner interaction

## 🚨 Troubleshooting

### Performance Issues

**Problem**: Analysis taking too long
- ✅ **Solution**: Use `main_production.py` for fastest headless analysis
- ✅ **Alternative**: Reduce `max_retries=1` in WebsiteAnalyzer configuration
- ✅ **Check**: Ensure headless mode is enabled (`headless=True`)

**Problem**: Browser windows opening/closing repeatedly  
- ✅ **Solution**: Switch to production mode - browser runs completely headless
- ✅ **Check**: Verify using `main_production.py` not `main.py` or debug versions

### Cookie Collection Issues

**Problem**: Missing cookies compared to manual browser inspection
- ✅ **Expected**: Fresh browser session collects only cookies set during that visit
- ✅ **Note**: Your manual browser has existing cookies from previous visits
- ✅ **Enhancement**: Try `main_super_optimized.py` with browser warmup for more cookies

**Problem**: Third-party cookies not detected
- ✅ **Solution**: Enhanced detection now identifies Google, Facebook, Cloudflare cookies automatically
- ✅ **Configuration**: Ensure anti-detection is enabled for better success rates

### Technical Issues  

**Problem**: ChromeDriver errors
- ✅ **Solution**: Update Chrome browser to latest version
- ✅ **Auto-fix**: ChromeDriver is automatically downloaded and managed

**Problem**: WAF/Security blocking
- ✅ **Solution**: Enable anti-detection measures (`enable_anti_detection=True`)
- ✅ **Alternative**: Reduce retry attempts to avoid triggering rate limits

**Problem**: Memory issues
- ✅ **Solution**: Use headless mode to reduce memory usage
- ✅ **Alternative**: Process websites one at a time instead of batch processing

### Debug Mode

For detailed troubleshooting, use the debug version:

```bash
# Interactive debugging with visible browser
python main_debug.py
```

This allows you to:
- See exactly what the browser is doing
- Step through each scenario manually
- Identify banner detection issues
- Verify cookie collection in real-time

## 🔄 Version History & Optimizations

### v2.0 - Performance & Cookie Enhancement (Current)
- ⚡ **3-5x Performance Improvement**: Headless mode, session reuse, optimized waits
- 🍪 **Enhanced Cookie Collection**: Third-party cookie detection (Google, Facebook, Cloudflare)  
- 🎯 **Multiple Execution Modes**: Production, optimized, debug, and super-optimized variants
- 🔧 **Modular Architecture**: Separated concerns into specialized components
- 📋 **Comprehensive Testing**: 30+ unit tests with full coverage
- 🐛 **Improved Debugging**: Interactive debug mode with visible browser
- 📊 **Better Analysis**: Cookie categorization and change tracking

### v1.0 - Initial Release  
- 🔍 Basic cookie banner detection
- 📸 Screenshot storage  
- 🛡️ Anti-detection measures
- 🇵🇹 Portuguese language support

## 🚀 Performance Comparison

| Metric | v1.0 (Original) | v2.0 (Optimized) | Improvement |
|--------|----------------|------------------|-------------|
| **Analysis Speed** | ~23 min for 2 websites | ~8-12 min for 2 websites | **3x faster** |
| **Browser Windows** | Visible (distracting) | Headless (clean) | **100% hidden** |
| **Cookie Detection** | Basic (first-party) | Enhanced (all cookies) | **2-3x more cookies** |
| **Session Management** | New browser per scenario | Reused per website | **66% fewer restarts** |
| **Error Recovery** | 3 retries with long waits | 1-2 fast retries | **50-75% less waiting** |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run the test suite (`python -m unittest discover tests -v`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Setup

```bash
# Clone and setup development environment
git clone <repository-url>
cd crumbscan
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Run tests to verify setup
python -m unittest discover tests -v

# Use debug mode for development
python main_debug.py
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational and research purposes only. Always respect website terms of service, robots.txt files, and applicable privacy laws (GDPR, CCPA, etc.). Use responsibly and in compliance with all relevant regulations.

The authors are not responsible for any misuse of this software or any violations of website terms of service.

## 🙏 Acknowledgments

- **Selenium Team** - For the powerful web automation framework
- **Pydantic** - For excellent data validation and parsing
- **Chrome DevTools** - For browser automation capabilities  
- **Portuguese Community** - For language-specific cookie banner patterns

---

## 📈 Quick Start Examples

### Production Analysis (Recommended)
```bash
python main_production.py  # Fast, headless, production-ready
```

### Debug a Specific Site
```python
analyzer = WebsiteAnalyzer("https://problematic-site.com", headless=False)
result = analyzer.analyze(CookieBannerAction.ACCEPT_ALL)
```

### Batch Process with Custom Config
```python
websites = ["https://site1.com", "https://site2.com"] 
for url in websites:
    analyzer = WebsiteAnalyzer(url, max_retries=1, headless=True)
    analyzer._setup_driver()
    for action in [CookieBannerAction.ACCEPT_ALL, CookieBannerAction.REJECT_ALL]:
        result = analyzer._analyze_with_existing_driver(action)
        print(f"{url} - {action.value}: {len(result.cookies)} cookies")
    analyzer._teardown_driver()
```

---

**Made with ❤️ for privacy research and GDPR compliance analysis**
