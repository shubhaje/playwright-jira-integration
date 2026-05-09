from playwright.sync_api import sync_playwright
import re
import time

class PageExtractor:
    def __init__(self, headless=True, timeout=30000):
        self.headless = headless
        self.timeout  = timeout

    def extract(self, url):
        print(f"🔍 Extracting page context: {url}")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(viewport={"width": 1280, "height": 800})
            page    = context.new_page()

            page.route("**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2,ttf}",
                       lambda route: route.abort())

            try:
                page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
                page.wait_for_load_state("networkidle", timeout=15000)
                time.sleep(1)

                context_data = {
                    "url":      page.url,
                    "title":    page.title(),
                    "headings": self._extract_headings(page),
                    "buttons":  self._extract_buttons(page),
                    "inputs":   self._extract_inputs(page),
                    "forms":    self._extract_forms(page),
                    "links":    self._extract_links(page),
                    "errors":   self._extract_errors(page),
                    "text":     self._extract_text(page),
                }

                self._print_summary(context_data)
                return context_data

            except Exception as e:
                print(f"❌ Extraction failed: {e}")
                return None

            finally:
                browser.close()

    def _extract_headings(self, page):
        js = "() => Array.from(document.querySelectorAll('h1,h2,h3,h4')).map(h => ({ level: h.tagName, text: h.innerText.trim() })).filter(h => h.text.length > 0)"
        return page.evaluate(js)

    def _extract_buttons(self, page):
        js = "() => Array.from(document.querySelectorAll('button, input[type=submit], input[type=button], [role=button]')).map(b => ({ text: (b.innerText || b.value || b.getAttribute('aria-label') || '').trim(), type: b.type || b.tagName, id: b.id || '', disabled: b.disabled || false })).filter(b => b.text.length > 0)"
        return page.evaluate(js)

    def _extract_inputs(self, page):
        js = "() => Array.from(document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([type=button]), textarea, select')).map(i => ({ type: i.type || i.tagName.toLowerCase(), name: i.name || '', id: i.id || '', placeholder: i.placeholder || '', required: i.required || false }))"
        return page.evaluate(js)

    def _extract_forms(self, page):
        js = "() => Array.from(document.querySelectorAll('form')).map(f => ({ id: f.id || '', action: f.action || '', method: f.method || 'get', fields: Array.from(f.querySelectorAll('input,textarea,select')).map(i => i.name || i.id || i.type).filter(Boolean) }))"
        return page.evaluate(js)

    def _extract_links(self, page):
        js = "() => Array.from(document.querySelectorAll('a[href]')).map(a => ({ text: a.innerText.trim(), href: a.href })).filter(a => a.text.length > 0 && !a.href.startsWith('mailto') && !a.href.startsWith('javascript')).slice(0, 20)"
        return page.evaluate(js)

    def _extract_errors(self, page):
        js = "() => Array.from(document.querySelectorAll('[class*=error],[class*=alert],[class*=warning],[role=alert]')).map(e => e.innerText.trim()).filter(t => t.length > 0)"
        return page.evaluate(js)

    def _extract_text(self, page):
        try:
            text = page.locator("body").inner_text()
            text = re.sub(r'\s+', ' ', text).strip()
            return text[:2000]
        except:
            return ""

    def _print_summary(self, ctx):
        print(f"✅ Page    : {ctx['title']}")
        print(f"   URL     : {ctx['url']}")
        print(f"   Headings: {len(ctx['headings'])}")
        print(f"   Buttons : {len(ctx['buttons'])}")
        print(f"   Inputs  : {len(ctx['inputs'])}")
        print(f"   Forms   : {len(ctx['forms'])}")
        print(f"   Links   : {len(ctx['links'])}")
        print(f"   Errors  : {len(ctx['errors'])}")