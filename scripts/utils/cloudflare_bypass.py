import cloudscraper
import time
import random
import os
import shutil
from typing import Optional, Dict, Any
from fake_useragent import UserAgent

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.firefox.service import Service as FirefoxService
    
    # Try webdriver-manager for automatic driver management
    try:
        from webdriver_manager.firefox import GeckoDriverManager
        from webdriver_manager.chrome import ChromeDriverManager
        WEBDRIVER_MANAGER_AVAILABLE = True
    except ImportError:
        WEBDRIVER_MANAGER_AVAILABLE = False
    
    # Try to import undetected_chromedriver (optional, for better Chrome support)
    try:
        import undetected_chromedriver as uc
        UC_AVAILABLE = True
    except ImportError:
        UC_AVAILABLE = False
    
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    UC_AVAILABLE = False
    WEBDRIVER_MANAGER_AVAILABLE = False


class CloudflareBypass:
    """Handles Cloudflare bypass using cloudscraper and selenium fallback"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.ua = UserAgent()
        self.scraper = None
        self.driver = None
        self.method = None
        
    def _get_random_user_agent(self) -> str:
        """Get random user agent from config or generate one"""
        user_agents = self.config.get('user_agents', [])
        if user_agents:
            return random.choice(user_agents)
        return self.ua.random
    
    def _init_cloudscraper(self) -> cloudscraper.CloudScraper:
        """Initialize cloudscraper with custom settings"""
        return cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            },
            delay=10
        )
    
    def _init_selenium(self) -> Optional[Any]:
        """Initialize Selenium WebDriver (tries Chrome, then Firefox)"""
        if not SELENIUM_AVAILABLE:
            return None
        
        # Try Chrome first
        driver = self._try_chrome()
        if driver:
            print("   ✓ Using Chrome/Chromium")
            return driver
        
        # Fallback to Firefox
        driver = self._try_firefox()
        if driver:
            print("   ✓ Using Firefox")
            return driver
        
        # Neither worked
        print("\n❌ Failed to initialize any browser")
        print("   Tried: Chrome, Firefox")
        print("\n   Please ensure one of these is installed:")
        print("     Chrome:   google-chrome-stable --version")
        print("     Firefox:  firefox --version\n")
        return None
    
    def _find_chrome_binary(self):
        """Find Chrome/Chromium binary path"""
        possible_paths = [
            '/usr/bin/google-chrome-stable',
            '/usr/bin/google-chrome',
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser',
            shutil.which('google-chrome-stable'),
            shutil.which('google-chrome'),
            shutil.which('chromium'),
            shutil.which('chromium-browser'),
        ]
        
        for path in possible_paths:
            if path and os.path.exists(path):
                return path
        return None
    
    def _try_chrome(self):
        """Try to initialize Chrome WebDriver"""
        try:
            # First, try undetected_chromedriver (better for scraping)
            if UC_AVAILABLE:
                chrome_binary = self._find_chrome_binary()
                options = uc.ChromeOptions()
                options.add_argument('--headless=new')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument(f'user-agent={self._get_random_user_agent()}')
                
                if chrome_binary:
                    options.binary_location = chrome_binary
                
                driver = uc.Chrome(options=options, version_main=None)
                driver.set_page_load_timeout(self.config.get('retry', {}).get('timeout', 30))
                return driver
            
            # Fallback to standard Selenium Chrome
            chrome_binary = self._find_chrome_binary()
            if not chrome_binary:
                return None
            
            options = ChromeOptions()
            options.binary_location = chrome_binary
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument(f'user-agent={self._get_random_user_agent()}')
            
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(self.config.get('retry', {}).get('timeout', 30))
            return driver
            
        except Exception as e:
            # Chrome failed, will try Firefox
            return None
    
    def _try_firefox(self):
        """Try to initialize Firefox WebDriver"""
        try:
            firefox_binary = shutil.which('firefox')
            if not firefox_binary:
                return None
            
            options = FirefoxOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.set_preference('general.useragent.override', self._get_random_user_agent())
            
            # Try with webdriver-manager first (auto-installs geckodriver)
            if WEBDRIVER_MANAGER_AVAILABLE:
                service = FirefoxService(GeckoDriverManager().install())
                driver = webdriver.Firefox(service=service, options=options)
            else:
                driver = webdriver.Firefox(options=options)
                
            driver.set_page_load_timeout(self.config.get('retry', {}).get('timeout', 30))
            return driver
            
        except Exception as e:
            return None
    
    def get(self, url: str, max_retries: int = None, force_selenium: bool = False) -> Optional[str]:
        """
        Fetch URL with Cloudflare bypass
        Returns HTML content or None on failure
        
        Args:
            url: URL to fetch
            max_retries: Number of retry attempts
            force_selenium: Force use of Selenium (for JavaScript-rendered pages)
        """
        if max_retries is None:
            max_retries = self.config.get('retry', {}).get('max_attempts', 3)
        
        backoff_factor = self.config.get('retry', {}).get('backoff_factor', 2)
        
        # If forced to use Selenium (for Vue.js pages), skip cloudscraper
        if force_selenium:
            if not SELENIUM_AVAILABLE:
                print("\n" + "="*60)
                print("❌ SELENIUM REQUIRED BUT NOT AVAILABLE")
                print("="*60)
                print("This page requires JavaScript rendering (Vue.js).")
                print("Selenium packages are installed but Chrome/Chromium is missing.")
                print("\nInstall Chrome or Chromium:")
                print("  Ubuntu/Debian: sudo apt install chromium-browser")
                print("  macOS:         brew install --cask google-chrome")
                print("  Windows:       Download from https://www.google.com/chrome/")
                print("="*60 + "\n")
                return None
            return self._get_with_selenium(url)
        
        for attempt in range(max_retries):
            try:
                # Try cloudscraper first
                if self.scraper is None:
                    self.scraper = self._init_cloudscraper()
                
                self.method = 'cloudscraper'
                response = self.scraper.get(
                    url,
                    headers={'User-Agent': self._get_random_user_agent()},
                    timeout=self.config.get('retry', {}).get('timeout', 30)
                )
                
                if response.status_code == 200:
                    return response.text
                
                # If cloudscraper fails with 403/503, try selenium
                if response.status_code in [403, 503] and SELENIUM_AVAILABLE:
                    print(f"Cloudscraper failed ({response.status_code}), trying Selenium...")
                    return self._get_with_selenium(url)
                
            except Exception as e:
                print(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    # Last attempt with Selenium
                    if SELENIUM_AVAILABLE:
                        print("Final attempt with Selenium...")
                        return self._get_with_selenium(url)
        
        return None
    
    def _get_with_selenium(self, url: str) -> Optional[str]:
        """Fallback to Selenium for tough Cloudflare challenges"""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # Reinitialize driver on retry or if not available
                if self.driver is None or attempt > 0:
                    if self.driver is not None:
                        try:
                            self.driver.quit()
                        except:
                            pass
                        self.driver = None
                    
                    self.driver = self._init_selenium()
                    if self.driver is None:
                        return None
                
                self.method = 'selenium'
                self.driver.get(url)
                
                # Wait for page to load and Cloudflare challenge to complete
                time.sleep(5)
                
                # Wait for body element
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # For Vue.js pages, wait for the chapters container
                if 'chapters' in url:
                    try:
                        print(f"   Waiting for Vue.js to render chapters...")
                        # Wait much longer for Vue.js to fully execute and render
                        time.sleep(10)
                        
                        # Try to wait for actual chapter links (with book ID pattern)
                        try:
                            WebDriverWait(self.driver, 20).until(
                                lambda d: len(d.find_elements(By.CSS_SELECTOR, "a[href*='.html']")) > 5
                            )
                            print(f"   ✓ Chapter links detected")
                        except:
                            print(f"   ⚠ Timeout waiting for chapter links, proceeding anyway...")
                        
                        # Extra wait for any remaining JavaScript
                        time.sleep(5)
                    except Exception as e:
                        # Fallback if something goes wrong
                        print(f"   ⚠ Exception during wait: {e}")
                        time.sleep(10)
                else:
                    # Additional wait for dynamic content
                    time.sleep(2)
                
                return self.driver.page_source
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"   Selenium attempt {attempt + 1} failed, retrying...")
                    continue
                else:
                    print(f"Selenium failed: {e}")
                    return None
        
        return None
    
    def close(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        self.scraper = None
        self.driver = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
