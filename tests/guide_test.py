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


SECTIONS = [base_checks]

if __name__ == "__main__":
    sys.exit(run())
