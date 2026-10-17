"""Render the guide's downloadable PDFs from print views of the real sections.

Run: python3 -I tools/make-pdfs.py

Each PDF is the concatenation of every element carrying data-pdf="<name>" in
index.html. The SHA-256 of that source HTML is recorded in assets/pdf/MANIFEST.json
so the test harness can tell when a PDF is older than its source.
"""
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "pdf"
SITE = "jason-miles.github.io/genie-deployment-guide"
VERIFIED = "Last verified 17 Oct 2026"

PDFS = {
    "rollout-plan": "Rollout plan and tracker",
    "onboarding-checklist": "Technical onboarding checklist",
    "benchmark-checklist": "Benchmark checklist",
    "genie-one-agent-code": "Genie One vs Agent vs Code",
}


class _Sources(HTMLParser):
    """Collects the raw HTML of every <div data-pdf="..."> (divs nest by depth count)."""

    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.text = text
        self.lines = [0]
        for line in text.splitlines(keepends=True):
            self.lines.append(self.lines[-1] + len(line))
        self.found = {}
        self._name = None
        self._depth = 0
        self._start = 0

    def _offset(self):
        line, col = self.getpos()
        return self.lines[line - 1] + col

    def handle_starttag(self, tag, attrs):
        if tag != "div":
            return
        if self._name is None:
            name = dict(attrs).get("data-pdf")
            if name:
                self._name, self._depth, self._start = name, 1, self._offset()
        else:
            self._depth += 1

    def handle_endtag(self, tag):
        if tag != "div" or self._name is None:
            return
        self._depth -= 1
        if self._depth == 0:
            end = self._offset() + len("</div>")
            self.found.setdefault(self._name, []).append(self.text[self._start:end])
            self._name = None


def source_hashes(html):
    """Map each data-pdf name to the SHA-256 of its concatenated source HTML."""
    parser = _Sources(html)
    parser.feed(html)
    return {n: hashlib.sha256("\n".join(parts).encode()).hexdigest() for n, parts in parser.found.items()}


PRINT_VIEW = """([name, title, sub]) => {
  const parts = [...document.querySelectorAll(`[data-pdf="${name}"]`)].map(e => e.cloneNode(true));
  document.documentElement.dataset.theme = 'light';
  const doc = document.createElement('div');
  doc.className = 'pdf-doc';
  const h = document.createElement('h1'); h.textContent = title;
  const p = document.createElement('p'); p.className = 'pdf-sub'; p.textContent = sub;
  doc.append(h, p, ...parts);
  document.body.replaceChildren(doc);
}"""

FOOTER = (
    '<div style="width:100%;font-size:8px;color:#555;padding:0 18mm;display:flex;justify-content:space-between">'
    f'<span>Genie deployment guide &middot; {SITE}</span>'
    '<span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>'
)


def main():
    from playwright.sync_api import sync_playwright

    html = (ROOT / "index.html").read_text()
    hashes = source_hashes(html)
    missing = [n for n in PDFS if n not in hashes]
    if missing:
        raise SystemExit(f"No data-pdf source in index.html for: {missing}")
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {}
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, title in PDFS.items():
            page = browser.new_page()
            page.goto((ROOT / "index.html").as_uri())
            page.wait_for_load_state("networkidle")
            page.emulate_media(media="print")
            page.evaluate(PRINT_VIEW, [name, title, f"Genie deployment guide. {VERIFIED}."])
            page.pdf(path=str(OUT / f"{name}.pdf"), format="A4", print_background=True,
                     margin={"top": "18mm", "bottom": "20mm", "left": "18mm", "right": "18mm"},
                     display_header_footer=True, header_template="<span></span>", footer_template=FOOTER)
            page.close()
            manifest[f"{name}.pdf"] = {"source": name, "sha256": hashes[name]}
        browser.close()
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {len(manifest)} PDFs to {OUT}")


if __name__ == "__main__":
    main()
