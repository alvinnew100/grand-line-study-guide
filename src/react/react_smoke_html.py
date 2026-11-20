"""Author-side helper: load every html-run block of the react lessons in headless Chromium,
click each button once and report page errors.

  python src/react/react_smoke_html.py
"""
import glob, os, re, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
bad = 0
with sync_playwright() as p:
    browser = p.chromium.launch()
    for f in sorted(glob.glob(os.path.join(HERE, "lessons", "*.md"))):
        text = open(f, encoding="utf-8").read()
        for i, html in enumerate(re.findall(r"```html-run\s*\n(.*?)```", text, re.S)):
            page = browser.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.set_content("<!doctype html><html><body>" + html + "</body></html>")
            page.wait_for_timeout(700)
            try:
                for inp in page.query_selector_all("input:not([type=checkbox])")[:2]:
                    inp.fill("ri")
                    page.wait_for_timeout(100)
                for n in range(min(len(page.query_selector_all("button")), 8)):
                    buttons = page.query_selector_all("button")
                    if n < len(buttons) and buttons[n].is_visible() and buttons[n].is_enabled():
                        buttons[n].click(timeout=1000)
                        page.wait_for_timeout(150)
            except Exception as e:  # noqa: BLE001
                errors.append("interaction: " + str(e).splitlines()[0])
            page.wait_for_timeout(1500)
            body = page.inner_text("body").strip()
            if not body:
                errors.append("empty body")
            name = f"{os.path.basename(f)} #{i + 1}"
            print(("FAIL " if errors else "ok   ") + name + ("  " + " | ".join(errors[:3]) if errors else ""))
            bad += bool(errors)
            page.close()
    browser.close()
print(bad, "page(s) with errors")
sys.exit(1 if bad else 0)
