#playwright page 
from playwright.sync_api import sync_playwright
import time

class BrowserCrawler:
    def __init__(self, headless=True, timeout=30000):
        self.headless = headless
        self.timeout  = timeout

    def crawl(self, url):
        """
        Navigate to a URL and return raw page data.
        Returns a dict with html, title, url, screenshot_path.
        """
        print(f"🌐 Crawling: {url}")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                )
            )
            page = context.new_page()

            try:
                # Navigate and wait until network is idle
                page.goto(url, timeout=self.timeout,
                          wait_until="domcontentloaded")
                page.wait_for_load_state("networkidle", timeout=15000)

                # Small pause for JS-rendered content
                time.sleep(1.5)

                # Capture screenshot
                screenshot_path = "browser_intelligence/last_screenshot.png"
                page.screenshot(path=screenshot_path, full_page=True)

                raw = {
                    "url":             page.url,
                    "title":           page.title(),
                    "html":            page.content(),
                    "screenshot_path": screenshot_path,
                }

                print(f"✅ Crawled: {raw['title']} ({raw['url']})")
                return raw

            except Exception as e:
                print(f"❌ Crawl failed: {e}")
                return None

            finally:
                browser.close()