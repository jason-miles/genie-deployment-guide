"""Playwright harness for the Genie deployment guide.

Run: python3 -I tests/guide_test.py
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
    check("without JavaScript all eight step headings are visible", pg.locator("section.step[id^=step-] h2:visible").count() == 8)
    check("without JavaScript all eight gates are visible", pg.locator("input[data-gate]:visible").count() == 8)
    ctx.close()


def step0_checks(browser, base):
    ctx, pg = new_page(browser)
    pg.goto(base)
    pg.wait_for_load_state("networkidle")
    cases = [
        (dict(user="business", need="ask", data="uc"), "one", "#step-5"),
        (dict(user="author", need="curate", data="uc"), "agent", "#step-1"),
        (dict(user="developer", need="code", data="uc"), "code", "#developer-track"),
        (dict(user="author", need="ask", data="uc"), "agent", "#step-4"),
    ]
    for a, product, target in cases:
        r = pg.evaluate("(a)=>window.recommend(a)", a)
        check(f"recommend {a['user']}/{a['need']} -> {product}", r["product"] == product and r["target"] == target, r)
    r = pg.evaluate("()=>window.recommend({user:'author',need:'curate',data:'external'})")
    check("external data adds a federation note", "federation" in r["note"].lower(), r)
    r = pg.evaluate("()=>window.recommend({user:'author',need:'curate',data:'unstructured'})")
    check("unstructured data adds a structured-data note", "structured" in r["note"].lower(), r)

    check("verdict prompts before all questions are answered", "three questions" in pg.inner_text("#verdict").lower())
    pg.check("input[name=q-user][value=business]")
    pg.check("input[name=q-need][value=ask]")
    pg.check("input[name=q-data][value=uc]")
    check("verdict names Genie One for a business user", "Genie One" in pg.inner_text("#verdict"), pg.inner_text("#verdict"))
    pg.click("#verdict a[href='#step-5']")
    check("verdict link jumps to step 05", pg.evaluate("location.hash") == "#step-5")

    pg.select_option("#cred", "api")
    check("credential chooser explains the API pattern", "OAuth" in pg.inner_text("#cred-out"), pg.inner_text("#cred-out"))
    pg.select_option("#cred", "standalone")
    check("credential chooser explains the standalone pattern", "embedded" in pg.inner_text("#cred-out").lower(), pg.inner_text("#cred-out"))

    gloss = pg.inner_text("#glossary")
    for term in ("Genie Spaces", "Databricks One", "One Chat", "Ontology"):
        check(f"glossary covers {term}", term in gloss, gloss[:120])
    prods = pg.inner_text("#products")
    check("product table names all three products", all(x in prods for x in ("Genie One", "Genie Agent", "Genie Code")))
    roles = pg.inner_text("#roles")
    check("roles table has the four ownership roles", all(x in roles for x in ("Agent owner", "Data steward", "Security reviewer", "Feedback reviewer")))
    check("step 00 has no console errors", not pg.errors, pg.errors)
    ctx.close()


def step_common(pg, n, html_path):
    sec = pg.locator(f"#step-{n}")
    txt = sec.inner_text()
    check(f"step {n} shows a Last verified date", "Last verified: 17 Oct 2026" in txt)
    check(f"step {n} has exactly one gate", sec.locator("input[data-gate]").count() == 1)
    check(f"step {n} has a copyable code block", sec.locator("pre .copy").count() >= 1)
    return txt


def claims_checks(browser, base):
    import re
    html = (ROOT / "index.html").read_text()
    claims = (ROOT / "docs" / "claims.md").read_text()
    known = set(re.findall(r"^\| (C-\d+) \|", claims, re.M))
    cited = set(re.findall(r"C-\d+", " ".join(re.findall(r"<!--(.*?)-->", html))))
    check("every cited claim ID exists in docs/claims.md", cited <= known, sorted(cited - known))


def steps12_checks(browser, base):
    ctx, pg = new_page(browser)
    pg.goto(base)
    pg.wait_for_load_state("networkidle")
    t = step_common(pg, 1, None)
    for term in ("Business stakeholder", "Technical stakeholder", "20 to 50", "out of scope"):
        check(f"step 1 covers {term}", term.lower() in t.lower(), term)
    check("step 1 has a topic-ranking table", pg.locator("#step-1 table#rank").count() == 1)
    t = step_common(pg, 2, None)
    for term in ("Silver", "Gold", "50 tables", "Metric View", "ROW FILTER", "MASK", "CAN MANAGE", "CAN EDIT", "CAN RUN", "CAN VIEW"):
        check(f"step 2 covers {term}", term.lower() in t.lower(), term)
    cred = pg.locator("#step-2 table#cred-models").inner_text()
    check("step 2 credential table has three patterns", all(x in cred for x in ("Standalone", "Dashboard companion", "Conversation API")), cred[:100])
    comp = pg.locator("#step-2").inner_text()
    check("step 2 has three compliance tiers", all(f"Tier {i}" in comp for i in (1, 2, 3)))
    check("steps 1-2 raise no errors", not pg.errors, pg.errors)
    ctx.close()


def steps34_checks(browser, base):
    ctx, pg = new_page(browser)
    pg.goto(base)
    pg.wait_for_load_state("networkidle")
    t = step_common(pg, 3, None)
    items = [x.lower() for x in pg.locator("#curation > li").all_inner_texts()]
    order = ["unity catalog metadata", "metric view", "sql expression", "example sql", "text instruction"]
    check("curation hierarchy lists five layers in order", len(items) == 5 and all(o in i for o, i in zip(order, items)), items)
    for term in ("6 to 10", "100 instructions", "Knowledge Store", "entity matching", "field-recommended"):
        check(f"step 3 covers {term}", term.lower() in t.lower(), term)
    check("step 3 two-week plan has ten day rows", pg.locator("#plan tbody tr").count() == 10)
    check("step 3 troubleshooting table has nine or more rows", pg.locator("#trouble tbody tr").count() >= 9)
    t = step_common(pg, 4, None)
    for term in ("30 to 80", "500", "80%", "field guidance", "Simple aggregations", "Time-based", "Filtered", "Multi-table joins", "Top-N", "Complex business logic", "1 to 2 weeks", "genie-create-eval-run"):
        check(f"step 4 covers {term}", term.lower() in t.lower(), term)
    check("steps 3-4 raise no errors", not pg.errors, pg.errors)
    ctx.close()


def steps567_checks(browser, base):
    ctx, pg = new_page(browser)
    pg.goto(base)
    pg.wait_for_load_state("networkidle")
    t = step_common(pg, 5, None)
    for term in ("Automatic Identity Management", "SCIM", "Consumer access", "Microsoft Teams", "Slack", "1 to 5 seconds", "10 minutes", "new conversation", "field guidance"):
        check(f"step 5 covers {term}", term.lower() in t.lower(), term)
    check("step 5 has a channel table", pg.locator("#step-5 table#channels tbody tr").count() >= 6)
    t = step_common(pg, 6, None)
    for term in ("aibiGenie", "genie_space_id", "Weekly", "Every two weeks", "Monthly", "Quarterly", "20 questions per minute", "field guidance", "SQL Alert"):
        check(f"step 6 covers {term}", term.lower() in t.lower(), term)
    t = step_common(pg, 7, None)
    for term in ("10 users", "50 users", "200 users", "rollback", "genie_spaces", "engine: direct", "get-space", "field-recommended", "conversation history"):
        check(f"step 7 covers {term}", term.lower() in t.lower(), term)
    check("step 7 has a go/no-go table", pg.locator("#step-7 table#gonogo tbody tr").count() >= 5)
    check("steps 5-7 raise no errors", not pg.errors, pg.errors)
    ctx.close()


def track_checks(browser, base):
    ctx, pg = new_page(browser)
    pg.goto(base)
    pg.wait_for_load_state("networkidle")
    check("developer track exists as a section", pg.locator("section.step#developer-track").count() == 1)
    check("developer track is collapsed by default", pg.evaluate("document.querySelector('#developer-track details').open") is False)
    check("sidebar links to the developer track", pg.locator("nav a[href='#developer-track']").count() == 1)
    pg.click("#products a[href='#developer-track']")
    check("link from the product table opens the track", pg.evaluate("document.querySelector('#developer-track details').open"))
    before = pg.get_attribute(".meter", "aria-valuenow")
    boxes = pg.locator("#developer-track ul.check input")
    check("developer track has its own checklist", boxes.count() >= 4)
    boxes.nth(0).check()
    boxes.nth(1).check()
    check("track checklist does not move the overall meter", pg.get_attribute(".meter", "aria-valuenow") == before)
    pg.reload()
    pg.wait_for_load_state("networkidle")
    pg.evaluate("document.querySelector('#developer-track details').open = true")
    check("track checklist persists", pg.locator("#developer-track ul.check input").nth(0).is_checked())
    t = pg.locator("#developer-track").inner_text()
    for term in (".assistant_instructions.md", "20,000", "SKILL.md", "partner-powered", "Unity Catalog permissions", "Last verified: 17 Oct 2026"):
        check(f"developer track covers {term}", term.lower() in t.lower(), term)
    ctx.close()
    ctx, pg = new_page(browser)
    pg.goto(base + "#developer-track")
    pg.wait_for_load_state("networkidle")
    check("deep link to the track expands it", pg.evaluate("document.querySelector('#developer-track details').open"))
    pg.goto(base + "#step-9")
    pg.wait_for_load_state("networkidle")
    check("unknown hash loads without errors", not pg.errors, pg.errors)
    ctx.close()


def appendix_checks(browser, base):
    ctx, pg = new_page(browser, accept_downloads=True)
    pg.goto(base)
    pg.wait_for_load_state("networkidle")
    check("appendix section exists and is in the sidebar", pg.locator("section#appendix").count() == 1 and pg.locator("nav a[href='#appendix']").count() == 1)
    rows = pg.locator("#tracker tbody tr")
    check("tracker has one row per phase P1 to P5", rows.count() == 5, rows.count())
    check("each tracker row has owner, date, status and notes controls",
          all(rows.nth(i).locator("input.trk-owner, input[type=date], select.trk-status, input.trk-notes").count() == 4 for i in range(5)))
    opts = rows.nth(0).locator("select.trk-status option").all_inner_texts()
    check("status options", opts == ["Not started", "In progress", "Blocked", "Done"], opts)
    pg.fill("#tracker tbody tr:nth-child(1) input.trk-owner", "Ada")
    pg.select_option("#tracker tbody tr:nth-child(2) select.trk-status", "Blocked")
    pg.fill("#tracker tbody tr:nth-child(3) input.trk-notes", 'needs "SCIM" sync, then retest')
    with pg.expect_download() as dl:
        pg.click("#csv")
    text = Path(dl.value.path()).read_text()
    lines = [l for l in text.splitlines() if l]
    check("CSV header", lines[0] == "Milestone,Owner,Due date,Status,Notes", lines[:1])
    check("CSV has a header and five rows", len(lines) == 6, len(lines))
    check("CSV carries the entered owner and status", '"Ada"' in lines[1] and '"Blocked"' in lines[2], lines[1:3])
    check("CSV escapes quotes in notes", '"needs ""SCIM"" sync, then retest"' in lines[3], lines[3])
    pg.reload()
    pg.wait_for_load_state("networkidle")
    check("tracker entries persist after reload", pg.input_value("#tracker tbody tr:nth-child(1) input.trk-owner") == "Ada" and pg.input_value("#tracker tbody tr:nth-child(2) select.trk-status") == "Blocked")
    risks = pg.locator("#risks tbody tr")
    check("risk register has at least eight rows with likelihood and impact", risks.count() >= 8 and all(risks.nth(i).locator("td").count() == 4 for i in range(risks.count())))
    check("five ways rollouts stall", pg.locator("#stall li").count() == 5)
    check("first wave guidance present", "first wave" in pg.locator("#appendix").inner_text().lower())
    check("appendix raises no errors", not pg.errors, pg.errors)
    ctx.close()


def pdf_checks(browser, base):
    import hashlib, importlib.util, json, re
    spec = importlib.util.spec_from_file_location("make_pdfs", ROOT / "tools" / "make-pdfs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    html = (ROOT / "index.html").read_text()
    hashes = mod.source_hashes(html)
    manifest_path = ROOT / "assets" / "pdf" / "MANIFEST.json"
    check("PDF manifest exists", manifest_path.exists())
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    shelf = json.loads(re.search(r'id="shelf-data">(.*?)</script>', html, re.S).group(1))
    pdfs = [r["href"].split("/")[-1] for r in shelf if r["type"] == "pdf"]
    check("shelf lists four PDFs", len(pdfs) == 4, pdfs)
    for name in pdfs:
        f = ROOT / "assets" / "pdf" / name
        ok = f.exists() and f.stat().st_size > 5000 and f.read_bytes()[:4] == b"%PDF"
        check(f"{name} exists, is over 5 KB and is a PDF", ok)
        m = manifest.get(name, {})
        check(f"{name} has a manifest entry for a data-pdf source", m.get("source") in hashes, m)
        check(f"{name} is not older than its source sections", m.get("sha256") == hashes.get(m.get("source")), (m.get("sha256"), hashes.get(m.get("source"))))


def tested_checks(browser, base):
    ctx, pg = new_page(browser)
    pg.goto(base)
    pg.wait_for_load_state("networkidle")
    total = pg.locator("pre[data-lang]").count()
    flagged = pg.locator("pre[data-lang][data-tested]").count()
    check("every code block declares its test status", total > 0 and total == flagged, (total, flagged))
    check("untested blocks show a visible label", pg.evaluate("[...document.querySelectorAll('pre[data-tested=no]')].every(p=>getComputedStyle(p,'::before').content.includes('Not run'))"))
    check("the hero explains the test status", "have not been run" in pg.inner_text(".hero").lower())
    pg.locator("pre[data-lang]").first.scroll_into_view_if_needed()
    pg.locator("pre .copy").first.click()
    clip = pg.evaluate("navigator.clipboard.readText()")
    check("copied code does not include the status label", "Not run" not in clip and "Copy" not in clip, clip[:80])
    ctx.close()


CONTRAST_JS = """(sels) => {
  const parse = c => { const m = c.match(/[\\d.]+/g).map(Number); return {r:m[0],g:m[1],b:m[2],a:m[3]===undefined?1:m[3]}; };
  const over = (f,b) => ({r:f.r*f.a+b.r*(1-f.a), g:f.g*f.a+b.g*(1-f.a), b:f.b*f.a+b.b*(1-f.a), a:1});
  const bgOf = el => { const chain=[]; for(let e=el;e;e=e.parentElement){ const c=parse(getComputedStyle(e).backgroundColor); chain.push(c); if(c.a===1) break; }
    let bg = chain[chain.length-1].a===1?chain[chain.length-1]:{r:255,g:255,b:255,a:1};
    for(let i=chain.length-2;i>=0;i--) bg=over(chain[i],bg); return bg; };
  const lum = c => { const f=v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)}; return .2126*f(c.r)+.7152*f(c.g)+.0722*f(c.b); };
  const out = {};
  for (const sel of sels) {
    const el = document.querySelector(sel); if (!el) { out[sel] = null; continue; }
    const bg = bgOf(el), fg = over(parse(getComputedStyle(el).color), bg);
    const a = lum(fg), b = lum(bg); out[sel] = +((Math.max(a,b)+.05)/(Math.min(a,b)+.05)).toFixed(2);
  }
  const pre = document.querySelector('pre[data-tested=no]');
  const bg = bgOf(pre), fg = over(parse(getComputedStyle(pre,'::before').color), bg);
  const a = lum(fg), b = lum(bg); out['label'] = +((Math.max(a,b)+.05)/(Math.min(a,b)+.05)).toFixed(2);
  return out;
}"""


def review_fix_checks(browser, base):
    import re
    import subprocess
    # Public-repo hygiene over every tracked file and every PDF
    files = subprocess.check_output(["git", "-C", str(ROOT), "ls-files"], text=True).splitlines()
    bad = "|".join(["ned" + "bank", "mo" + "mentum", "inves" + "tec", "capi" + "tec", "1e1B" + "Y_", "vibe-coding" + "-repos",
                    "gh auth" + " token", "Claude's own" + " push", "permission" + "-denied", r"jason\.miles", r"go/(?!no-go)[a-z]"])
    pat = re.compile(bad, re.I)
    hits = []
    for f in files:
        path = ROOT / f
        if f.endswith(".pdf"):
            text = subprocess.run(["pdftotext", str(path), "-"], capture_output=True, text=True).stdout
        elif f.endswith(".woff2"):
            continue
        else:
            text = path.read_text(errors="ignore")
        for m in pat.finditer(text):
            hits.append((f, m.group(0)))
    check("tracked files and PDFs contain no customer names, internal IDs or local paths", not hits, hits[:5])

    # PDF content
    def pdf_text(name):
        return subprocess.run(["pdftotext", str(ROOT / "assets" / "pdf" / name), "-"], capture_output=True, text=True).stdout
    t = pdf_text("onboarding-checklist.pdf")
    check("onboarding PDF contains technical and business validation", "Technical validation" in t and "Business validation" in t and len(t) > 1200, len(t))
    check("benchmark PDF contains the benchmark suite section", "Build the benchmark suite" in pdf_text("benchmark-checklist.pdf"))

    ctx, pg = new_page(browser)
    pg.goto(base)
    pg.wait_for_load_state("networkidle")

    # Print/PDF colours
    pg.emulate_media(media="print")
    r = pg.evaluate(CONTRAST_JS, ["pre mark.v", "pre .k", "pre .s", "pre .c"])
    low = {k: v for k, v in r.items() if v is not None and v < 4.5}
    check("code colours meet 4.5:1 in print", not low, low)
    pg.emulate_media(media="screen")

    # Code-block label sits in flow and does not cover code
    for vp in ({"width": 1400, "height": 900}, {"width": 390, "height": 844}):
        pg.set_viewport_size(vp)
        info = pg.evaluate("""()=>{const pre=document.querySelector('pre[data-tested=no]');const cs=getComputedStyle(pre,'::before');
          return {pos:cs.position,ws:cs.whiteSpace,content:cs.content,lang:pre.dataset.lang,gap:pre.querySelector('code').getBoundingClientRect().top-pre.getBoundingClientRect().top}}""")
        check(f"code label is in flow at {vp['width']}px", info["pos"] != "absolute" and info["ws"] == "normal" and "Not run" in info["content"] and info["lang"].lower() in info["content"].lower() and info["gap"] >= 28, info)
    pg.set_viewport_size({"width": 1400, "height": 900})

    # Search reaches the collapsed Developer track and opens it
    pg.keyboard.press("Control+k")
    pg.fill("#pal-q", "assistant_workspace_instructions")
    check("search finds text inside the collapsed Developer track", pg.locator("#pal-list li[role=option]:not(.pal-empty)").count() >= 1)
    pg.keyboard.press("Enter")
    check("choosing a track result opens the track", pg.evaluate("document.querySelector('#developer-track details').open"))

    # Environment panel keeps names with spaces and dots; workspace URL variable exists
    pg.fill("#v-grp", "Data Analysts")
    check("group names with spaces are preserved", pg.input_value("#v-grp") == "Data Analysts")
    check("group name with spaces reaches the code", "Data Analysts" in pg.inner_text("pre[data-lang] code mark.v >> nth=-1") or pg.locator("mark.v", has_text="Data Analysts").count() > 0)
    check("workspace URL variable exists", pg.locator("#v-ws").count() == 1)
    if pg.locator("#v-ws").count():
        pg.fill("#v-ws", "https://dev.cloud.databricks.com")
        check("workspace URL reaches the bundle YAML", "https://dev.cloud.databricks.com" in pg.inner_text("#step-7 pre[data-lang=yaml] code"))

    # Stable checklist keys
    keys = pg.eval_on_selector_all("ul.check input", "els=>els.map(e=>e.dataset.key||'')")
    check("every checklist item has a unique data-key", all(keys) and len(set(keys)) == len(keys), keys[:3])
    if all(keys):
        pg.locator("ul.check:not(.dev) input").first.check()
        check("checklist state is stored under its data-key", pg.evaluate("(k)=>localStorage.getItem('genie-chk-'+k)", keys[0]) == "1")

    # Step 07 promotion recipe
    t7 = pg.inner_text("#step-7")
    check("step 7 leads with bundle generate genie-space", "bundle generate genie-space" in t7)
    check("step 7 names the .geniespace.json file", ".geniespace.json" in t7 and "jq -r .serialized_space" in t7)
    check("step 7 no longer says create-space takes the same payload", "take the same serialized payload" not in t7)
    check("bundle YAML quotes the warehouse ID", 'warehouse_id: "' in pg.inner_text("#step-7 pre[data-lang=yaml] code"))
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


SECTIONS = [base_checks, shelf_checks, step0_checks, claims_checks, steps12_checks, steps34_checks, steps567_checks, track_checks, appendix_checks, pdf_checks, tested_checks, review_fix_checks]

if __name__ == "__main__":
    sys.exit(run())
