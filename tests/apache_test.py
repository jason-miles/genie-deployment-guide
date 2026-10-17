"""Serve the repo with the system Apache 2.4 so .htaccess is exercised.

Run: python3 -I tests/apache_test.py
Exit code 0 only if every check passes. Skips (exit 0 with a notice) if /usr/sbin/httpd is absent.
"""
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
HTTPD = Path("/usr/sbin/httpd")
MODS = ["mpm_prefork", "filter", "setenvif", "authz_core", "mime", "dir", "deflate", "expires", "headers", "alias", "log_config", "unixd"]
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + name + (f" -> {detail}" if detail and not ok else ""))


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def fetch(url):
    try:
        with urllib.request.urlopen(url) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), b""


def main():
    if not HTTPD.exists():
        print("SKIP httpd not found")
        return 0
    tmp = Path(tempfile.mkdtemp(prefix="genie-apache-"))
    port = free_port()
    lines = ['ServerRoot "/usr"', "User " + Path.home().name, f"Listen 127.0.0.1:{port}", f"PidFile {tmp}/httpd.pid",
             f"ErrorLog {tmp}/error.log", "LogLevel warn", "ServerName localhost", "TypesConfig /etc/apache2/mime.types"]
    lines += [f"LoadModule {m}_module /usr/libexec/apache2/mod_{m}.so" for m in MODS]
    lines += [f'DocumentRoot "{ROOT}"', f'<Directory "{ROOT}">', "  AllowOverride All", "  Require all granted", "</Directory>"]
    conf = tmp / "httpd.conf"
    conf.write_text("\n".join(lines) + "\n")
    proc = subprocess.Popen([str(HTTPD), "-f", str(conf), "-DFOREGROUND"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            start_new_session=True)  # Apache signals its whole process group on stop
    time.sleep(1.5)
    base = f"http://127.0.0.1:{port}/"
    try:
        status, headers, _ = fetch(base)
        h = {k.lower(): v for k, v in headers.items()}
        check("index served with 200", status == 200, status)
        check("CSP header present", "content-security-policy" in h)
        check("nosniff header present", h.get("x-content-type-options", "").lower() == "nosniff", h)
        status, headers, body = fetch(base + "assets/pdf/rollout-plan.pdf")
        check("PDF served as application/pdf", status == 200 and headers.get("Content-Type", "").startswith("application/pdf") and body[:4] == b"%PDF", (status, headers.get("Content-Type")))
        status, headers, _ = fetch(base + "assets/icons/blog.svg")
        check("SVG icon served as image/svg+xml", status == 200 and headers.get("Content-Type", "").startswith("image/svg+xml"), headers.get("Content-Type"))
        check(".git is not exposed", fetch(base + ".git/config")[0] in (403, 404))
        check("directory listing is off", fetch(base + "assets/")[0] in (403, 404))
        with sync_playwright() as p:
            browser = p.chromium.launch()
            pg = browser.new_page()
            errors = []
            pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.goto(base)
            pg.wait_for_load_state("networkidle")
            check("no CSP or console errors under Apache", not errors, errors)
            check("shelf renders under the CSP", pg.locator("section.shelf a.res-card").count() >= 1)
            check("icons load under the CSP", pg.evaluate("[...document.querySelectorAll('.res-card img')].every(i=>i.complete&&i.naturalWidth>0)"))
            pg.keyboard.press("Control+k")
            check("search palette opens under the CSP", pg.evaluate("document.getElementById('palette').open"))
            browser.close()
    finally:
        proc.terminate()
        proc.wait(timeout=10)
    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
