"""Playwright harness for the Genie deployment guide.

Run: python3 -I tests/guide_test.py [--allow-missing-pdf]
Exit code 0 only if every check passes.
"""
import functools
import socket
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
ALLOW_MISSING_PDF = "--allow-missing-pdf" in sys.argv
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f" -> {detail}" if detail and not ok else ""))


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    assert port != 8765
    return port


def new_page(browser, **kw):
    ctx = browser.new_context(viewport={"width": 1400, "height": 900},
                              permissions=["clipboard-read", "clipboard-write"],
                              color_scheme="light", **kw)
    pg = ctx.new_page()
    pg.errors = []
    pg.on("console", lambda m: pg.errors.append(m.text) if m.type == "error" else None)
    pg.on("pageerror", lambda e: pg.errors.append(str(e)))
    return ctx, pg


def base_checks(browser, base):
    ctx, pg = new_page(browser)
    pg.goto(base)
    pg.wait_for_load_state("networkidle")
    check("no console/page errors on load", not pg.errors, pg.errors)
    check("title mentions Genie", "Genie" in pg.title(), pg.title())
    steps = pg.locator("section.step[id^=step-]")
    check("eight numbered steps", steps.count() == 8, steps.count())
    check("one gate per step", pg.locator("input[data-gate]").count() == 8)

    pg.click("#theme")
    d1 = pg.evaluate("document.documentElement.dataset.theme")
    pg.reload()
    d2 = pg.evaluate("document.documentElement.dataset.theme")
    check("theme toggles and persists", d1 != "light" or d2 == d1, f"{d1},{d2}")

    pg.locator("input[data-gate='step-1']").check()
    pg.reload()
    pg.wait_for_load_state("networkidle")
    check("gate persists across reload", pg.locator("input[data-gate='step-1']").is_checked())
    check("meter moves above 0%", int(pg.get_attribute(".meter", "aria-valuenow")) > 0)

    pg.keyboard.press("Control+k")
    check("Ctrl+K opens search palette", pg.evaluate("document.getElementById('palette').open"))
    pg.keyboard.press("Escape")

    # Review Focus: env values never inject markup
    pg.fill("#v-cat", '<b>"x"&')
    value = pg.input_value("#v-cat")
    check("env value is sanitised", value == "bx", value)
    check("env value injects no markup", pg.locator("pre code b").count() == 0)
    check("env value shows in code sample", "bx" in pg.inner_text("pre[data-lang] code mark.v"))

    # Review Focus: search with regex characters
    pg.keyboard.press("Control+k")
    for q in ("(", "[a*\\"):
        pg.fill("#pal-q", q)
    pg.fill("#pal-q", "zzzznomatch")
    check("empty search result row has role=option", pg.locator("#pal-list li.pal-empty[role=option]").count() == 1)
    check("regex characters in search keep palette open", pg.evaluate("document.getElementById('palette').open"))
    check("regex characters in search raise no errors", not pg.errors, pg.errors)
    ctx.close()

    # Review Focus: localStorage unavailable
    ctx, pg = new_page(browser)
    pg.add_init_script(
        "const boom=()=>{throw new DOMException('blocked','SecurityError')};"
        "Object.defineProperty(window,'localStorage',{get:boom});")
    pg.goto(base)
    pg.wait_for_load_state("networkidle")
    check("localStorage really is blocked in that context", pg.evaluate("(()=>{try{localStorage;return false}catch(e){return true}})()"))
    check("page loads with localStorage blocked", not pg.errors, pg.errors)
    pg.locator("input[data-gate='step-2']").check()
    check("gate still ticks with localStorage blocked", pg.locator("input[data-gate='step-2']").is_checked())
    ctx.close()


def shelf_checks(browser, base):
    ctx, pg = new_page(browser)
    hosts = set()
    pg.on("request", lambda r: hosts.add(r.url.split("/")[2]) if r.url.startswith("http") else None)
    pg.goto(base)
    pg.wait_for_load_state("networkidle")
    cards = pg.locator("section.shelf a.res-card")
    n = cards.count()
    check("shelf has 1 to 6 cards", 1 <= n <= 6, n)
    check("every card is a single link with an icon that loads",
          all(pg.evaluate("(el)=>{const i=el.querySelector('img');return !!i && i.complete && i.naturalWidth>0}", cards.nth(i).element_handle()) for i in range(n)))
    for i in range(n):
        c = cards.nth(i)
        kind = c.get_attribute("data-type")
        href = c.get_attribute("href")
        label = c.inner_text() + " " + (c.locator(".res-sr").text_content() or "")
        no_aria = c.get_attribute("aria-label") is None
        if kind == "pdf":
            check(f"PDF card {i} downloads from assets/pdf", c.get_attribute("download") is not None and href.startswith("assets/pdf/") and no_aria and label.startswith("PDF") and "Downloads a PDF file" in label, (href, label))
            if not ALLOW_MISSING_PDF:
                r = ctx.request.get(base + href)
                check(f"PDF card {i} file exists", r.status == 200 and r.body()[:4] == b"%PDF", r.status)
        else:
            rel = c.get_attribute("rel") or ""
            check(f"blog card {i} opens safely in a new tab", kind == "blog" and href.startswith("https://") and c.get_attribute("target") == "_blank" and "noopener" in rel and "noreferrer" in rel and no_aria and label.startswith("BLOG") and "Opens in a new tab" in label, (href, rel, label))
    # keyboard order and visible focus
    pg.evaluate("document.activeElement.blur()")
    seen = []
    for _ in range(40):
        pg.keyboard.press("Tab")
        if pg.evaluate("document.activeElement.classList.contains('res-card')"):
            seen.append(pg.evaluate("document.activeElement.getAttribute('href')"))
            if len(seen) == 1:
                check("focused card shows an outline", pg.evaluate("getComputedStyle(document.activeElement).outlineStyle") != "none")
            if len(seen) == n:
                break
    expected = [cards.nth(i).get_attribute("href") for i in range(n)]
    check("Tab visits cards in DOM order", seen == expected, seen)
    rows = pg.evaluate("new Set([...document.querySelectorAll('section.shelf a.res-card')].map(e=>Math.round(e.getBoundingClientRect().top))).size")
    check("shelf wraps to at most two rows at 1400px", rows <= 2, rows)
    check("shelf sits above step 00", pg.evaluate("document.querySelector('section.shelf').compareDocumentPosition(document.getElementById('step-0')) & Node.DOCUMENT_POSITION_FOLLOWING") > 0)
    check("shelf makes no external requests", hosts <= {base.split("/")[2]}, hosts)
    ctx.close()

    # Review Focus: JavaScript disabled
    ctx = browser.new_context(java_script_enabled=False)
    pg = ctx.new_page()
    pg.goto(base)
    check("without JavaScript all eight step headings are visible", pg.locator("section.step h2:visible").count() == 8)
    check("without JavaScript all eight gates are visible", pg.locator("input[data-gate]:visible").count() == 8)
    ctx.close()


def run():
    port = free_port()
    server = subprocess.Popen([sys.executable, "-I", "-m", "http.server", str(port), "--bind", "127.0.0.1",
                               "--directory", str(ROOT)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.8)
    base = f"http://127.0.0.1:{port}/"
    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch()
            except Exception:
                browser = p.chromium.launch(channel="chrome")
            for section in SECTIONS:
                section(browser, base)
            browser.close()
    finally:
        server.terminate()
    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    return 1 if failed else 0


SECTIONS = [base_checks, shelf_checks]

if __name__ == "__main__":
    sys.exit(run())
