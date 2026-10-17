# Genie Deployment Guide Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and publish a static, public Genie deployment guide (steps 00 to 07, Developer track, tracker, resource shelf, generated PDFs) in the format of the UC migration guide.

**Architecture:** Copy the UC guide's static shell (`index.html`, `assets/css/style.css`, `assets/js/app.js`, fonts, `.htaccess`) into this repo and rename its storage keys. Content is hand-written HTML sections, one per step, each ending in a persisted gate. A JSON block in `index.html` drives the resource shelf; `tools/make-pdfs.py` renders committed PDFs from print views of the real sections. A Python Playwright harness in `tests/` gates every commit.

**Tech Stack:** HTML, CSS, vanilla JS (no build, no external requests), Python 3 Playwright (`python3 -I`), axe-core via `npm pack`, Apache 2.4 for `.htaccess` testing.

**Spec:** `docs/superpowers/specs/2026-10-17-genie-deployment-guide-design.md`
**Template repo (read-only reference):** `the sibling UC migration guide repo` (files `index.html`, `assets/css/style.css`, `assets/js/app.js`, `.htaccess`, `.databricks-impeccable.md`). Old harness: `a local script`, the axe and contrast scripts (may be gone; recreate from the descriptions in Task 1 if missing).

## Global Constraints

- Palette: Lava 600 `#FF3621` (10% accent), Navy 900 `#0B2026`, Light `#F9F7F4`. Fonts: DM Sans 400/500/700 and DM Mono, local files only.
- No build step at runtime, no external network requests, strict CSP from `.htaccess` stays valid.
- WCAG AA; axe-core zero violations in light and dark; no side-stripes; no `content-visibility:auto`.
- Public repo: no customer names, person names, `go/` links, internal Slack channels, Salesforce or internal doc links.
- Resource shelf: at most 6 cards; PDF cards use `download`, blog cards use `target="_blank" rel="noopener noreferrer"`.
- Label numbers "Databricks-published" or "field-recommended". Genie Code content from public docs only.
- Every volatile fact has a row in `docs/claims.md` and a "Last verified" date in the step.
- Test server: never port 8765. Run Python as `python3 -I`. Gate every commit on the harness exit code, never a `;` chain.
- Commit messages end with `Co-authored-by: Isaac <no-reply@databricks.com>`. Never use `--no-verify` or `-n` on commit. Claude does not push; the user runs `! git push origin main`.
- Never auto-select a Databricks profile; the user names it. Untested commands are marked "untested".

## Review Focus

- Environment-panel values containing `<`, `>`, `&` or quotes must show literally in code samples and never inject markup (Task 1 test).
- `localStorage` unavailable (private mode or blocked): page loads, gates still tick for the session, no console error (Task 1 test).
- Search query containing regex characters (`(`, `[`, `*`, `\`): palette stays open, no exception (Task 1 test).
- JavaScript disabled: all step text, commands and gates are readable; only the shelf and enhancements are absent (Task 3 test).
- Deep link to an unknown hash (`#step-9`) or a hash for a collapsed Developer track: page loads, no exception, track expands for its own hash (Task 8 test).

## File Structure

| Path | Responsibility |
|---|---|
| `index.html` | All content: shelf JSON block, steps 00 to 07, Developer track, tracker, risks |
| `assets/css/style.css` | Template styles plus `.shelf`, `.card`, `.chooser` additions |
| `assets/js/app.js` | Template behaviour (theme, nav, gates, env panel, search, progress); keys renamed `genie-` |
| `assets/js/shelf.js` | `renderShelf(resources)`: builds cards from the JSON block |
| `assets/icons/*.svg` | Original card icons |
| `assets/pdf/*.pdf`, `assets/pdf/MANIFEST.json` | Generated PDFs and source hashes |
| `tools/make-pdfs.py` | Dev-time PDF renderer and manifest writer |
| `tests/guide_test.py` | Playwright harness; `tests/axe.py`, `tests/contrast.py` |
| `docs/claims.md` | Claims register |
| `README.md`, `LICENSE`, `.htaccess`, `.nojekyll`, `.databricks-impeccable.md` | Repo files |

---

### Task 1: Scaffold shell, harness and baseline tests

**Files:**
- Create: everything under "Template" copies below, `tests/guide_test.py`, `tests/axe.py`, `tests/contrast.py`, `index.html` (skeleton)
- Copy from template: `assets/css/style.css`, `assets/js/app.js`, `assets/fonts/*`, `assets/favicon.svg`, `LICENSE`, `.htaccess`, `.nojekyll`, `.databricks-impeccable.md`

**Interfaces:**
- Produces: `tests/guide_test.py` exposing `def run() -> int` (exit code) and section functions `def base_checks(page, base)`, later `shelf_checks`, `step_checks`, `pdf_checks`, each calling `check(name: str, ok: bool)` which records a failure and prints `PASS/FAIL name`. Skeleton `index.html` with `<section class="step" id="step-N">` for N=0..7, a `<label class="gate"><input type="checkbox" data-gate="step-N">` per step, nav `<li><a href="#step-N">`, and the template's sidebar, env panel and search markup.
- `app.js` storage keys become `genie-theme`, `genie-gate-<id>`, `genie-chk-<i>`, env key `genie-env`.

- [ ] **Step 1: Write the failing tests** in `tests/guide_test.py`: `base_checks` asserts page title contains "Genie", 8 `.step` sections and 8 gates, theme toggle flips `data-theme`, ticking a gate persists across reload and moves the meter above 0%, Ctrl+K opens the palette, and the three Review Focus cases: env value `<b>"x"&` renders as literal text in a code sample (no `<b>` element inside `pre code`), blocking `localStorage` via `add_init_script` leaves zero console errors and gates tick, searching `(` then `[a*\` leaves the palette open with zero page errors.
- [ ] **Step 2: Run to verify failure** — `python3 -I tests/guide_test.py` → FAIL (no `index.html`).
- [ ] **Step 3: Copy template files**, rename storage keys with `sed` on `app.js`, write skeleton `index.html` (title "Genie Deployment Guide", brand text "Genie deployment", filter placeholder updated, one placeholder sentence per step), rewrite `.databricks-impeccable.md` (audience: Field SAs/DSAs; use case: follow eight steps for a Genie Agent rollout; same brand block). Harness starts `python3 -I -m http.server` on a free port other than 8765.
- [ ] **Step 4: Port axe and contrast scripts** into `tests/`: `axe.py` loads page in light and dark, injects `axe.min.js` (from `npm pack axe-core` extracted to a temp dir, path passed as argv[1]) and exits non-zero on any violation; `contrast.py` computes text/background ratios for the palette tokens and exits non-zero below 4.5 (3.0 for large text).
- [ ] **Step 5: Run** `python3 -I tests/guide_test.py` → all PASS; `python3 -I tests/axe.py <axe-dir>` → 0 violations.
- [ ] **Step 6: Commit** `feat: scaffold guide shell, harness and baseline tests`

### Task 2: Claims register and fact verification

**Files:**
- Create: `docs/claims.md`

**Interfaces:**
- Produces: `docs/claims.md` table with columns `ID | Claim | Source | Status (verified/unverified/conflicting) | Verified on`. Later tasks cite IDs as `C-nn` in an HTML comment beside the fact and in the step's "Last verified" line.

- [ ] **Step 1: List claims**, one row each, from the spec §7 and the text exports of the source documents (not published): UI limit 20 questions/min and API free tier 5/min; 30-table limit; 500 benchmarks per space; 80% accuracy guidance; Space to Agent rename; Databricks One to Genie One naming; native bundle support for Agents (conflicting sources); Share-to-Account-Users preview status; consumer-access default toggle status; AIM GA and default date; customer-managed keys cutoff; audit `service_name = 'aibiGenie'`; `system.query.history` `query_source.genie_space_id`; Ontology, Domains and Pages definitions; Genie Code feature set and enablement.
- [ ] **Step 2: Verify each** against current public docs using the `databricks-docs` skill (`llms.txt` index) and web search; set status and date. Where docs cannot confirm, status `unverified` and the step text must say so.
- [ ] **Step 3: Verification check** — `grep -c "| unverified |\|| conflicting |" docs/claims.md` returns 0 conflicting (all conflicts resolved with a cited source); unverified rows are listed in the commit message.
- [ ] **Step 4: Commit** `docs: add claims register`

### Task 3: Resource shelf

**Files:**
- Create: `assets/js/shelf.js`, `assets/icons/{blog,pdf-rollout,pdf-checklist,pdf-benchmark,pdf-compare,blog-2}.svg`
- Modify: `index.html` (shelf JSON block and `<section class="shelf" aria-label="Resources">` above step 0), `assets/css/style.css`, `tests/guide_test.py`

**Interfaces:**
- Consumes: Task 1 harness.
- Produces: `<script type="application/json" id="shelf-data">[{"type":"pdf"|"blog","title":str,"href":str,"icon":str,"blurb":str}]</script>`; `function renderShelf(resources: Resource[], root: HTMLElement): void` in `shelf.js`, loaded with `<script src>` (CSP-safe). PDF hrefs point to `assets/pdf/<name>.pdf`, which Task 10 generates; until then the PDF existence check is skipped via a `--allow-missing-pdf` flag removed in Task 10.

- [ ] **Step 1: Write failing `shelf_checks`**: card count between 1 and 6; each card is one `<a>`; PDF cards have `download`, blog cards have `target=_blank` and `rel` containing `noopener noreferrer`; every blog `href` starts `https://`; accessible name starts "Download PDF:" or "Opens blog post:"; Tab order follows DOM order and each card shows a visible focus ring (computed `outline-style` not `none`); with JavaScript disabled (`java_script_enabled=False`) all eight step headings and gates remain visible; no external requests (record `page.on("request")` hosts, only localhost).
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** `renderShelf` (creates `<a class="card">` with `<img alt="" src=icon>`, title, type badge), the six JSON entries (Genie One rollout playbook blog at `https://www.databricks.com/blog/how-roll-out-genie-one-step-step-enterprise-playbook`; four PDFs; one further public Databricks blog found in Task 2 research), six original SVG icons in the palette, and `.shelf/.card` CSS (single row wide, wraps, max two rows, light/dark safe).
- [ ] **Step 4: Run** → PASS; run `tests/axe.py` → 0 violations.
- [ ] **Step 5: Commit** `feat: add resource shelf`

### Task 4: Step 00, Choose your path

**Files:** Modify `index.html` (step-0 section), `assets/js/app.js` (chooser), `assets/css/style.css`, `tests/guide_test.py`

**Interfaces:**
- Produces: `function recommend(answers: {user: "business"|"author"|"developer", need: "ask"|"curate"|"code", data: "uc"|"external"|"unstructured"}): {product: "one"|"agent"|"code", target: string}` in `app.js`, where `target` is a step anchor (`#step-5`, `#step-1`, `#developer-track`). Glossary table, roles table, credential-model chooser, and controls list are static HTML in the section.

- [ ] **Step 1: Write failing tests**: `recommend({user:"business",need:"ask",data:"uc"})` → `{product:"one", target:"#step-5"}`; `{author,curate,uc}` → agent/`#step-1`; `{developer,code,uc}` → code/`#developer-track`; `{author,curate,external}` → agent with a text note about federation shown; clicking through the question flow in the UI shows the recommendation and its jump link navigates to the target; the glossary contains rows for Space→Agent, Databricks One→Genie One, One Chat→Genie chat, Ontology.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** the section from spec §2 and §3 (three-product table; question flow with radio groups; credential chooser covering standalone Agent, dashboard companion, Conversation API; roles: owner, data steward, security reviewer, feedback reviewer; controls). Cite claims IDs.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: add step 00 chooser, glossary and roles`

### Task 5: Steps 01 and 02 (Discover and scope; Data and governance)

**Files:** Modify `index.html`, `tests/guide_test.py`

**Interfaces:** Consumes `data-gate="step-1"` and `"step-2"` gates and env tokens from Task 1 (`catalog`, `schema`, `warehouse_id`, `space_id`, `group`).

- [ ] **Step 1: Write failing `step_checks(1)` and `step_checks(2)`**: each section has a "Last verified" date, one gate, at least one copyable code block with Copy button, every `C-nn` cited exists in `docs/claims.md`, and step 2 contains the three credential-model rows and the three compliance tiers.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Write step 01** from the field guide and Enterprise Pillar 1: topic ranking, good and bad topics, 20 to 50 questions, owner and RACI, success metrics; gate text from the lifecycle P0 exit criteria. **Write step 02** from Pillars 2 and 3: layer guidance (Silver/Gold), per-table must/should/good lists, Metric Views and Ontology, quality-gate table, UC grants SQL using env tokens (`GRANT SELECT ON ...`), row filter and column mask examples, access tiers CAN MANAGE/CAN RUN/CAN VIEW, compliance tiers. Strip per Global Constraints.
- [ ] **Step 4: Run** → PASS; run the strip scan: `grep -rEi "go/[a-z]|customer|customer|customer|@databricks\.com" index.html docs` returns only the rule text.
- [ ] **Step 5: Commit** `feat: add steps 01 and 02`

### Task 6: Steps 03 and 04 (Build; Benchmark and validate)

**Files:** Modify `index.html`, `tests/guide_test.py`

- [ ] **Step 1: Write failing `step_checks(3)` and `step_checks(4)`** with the same structure checks, plus: step 3 contains a 10-day table (two-week plan, weekdays) and the curation-hierarchy list in order (UC metadata, Metric Views, SQL expressions, parameterised example SQL, text instructions); step 4 states the 80% gate labelled "Databricks-published", the 30 to 80 benchmark range, the six benchmark categories, and the technical-then-business validation sequence with 1 to 2 weeks each labelled "field-recommended".
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Write step 03** from the two-week guide and Pillar 1.2 to 1.4 (Knowledge Store contents, sample questions 6 to 10, entity matching, join relationships, example SQL). **Write step 04** from Pillar 5.3 and the onboarding templates' Phases 1 and 2. Include the Agent export/get command with `--profile <profile>` placeholder, marked untested until Task 11 verification.
- [ ] **Step 4: Run** → PASS, strip scan clean.
- [ ] **Step 5: Commit** `feat: add steps 03 and 04`

### Task 7: Steps 05, 06 and 07

**Files:** Modify `index.html`, `tests/guide_test.py`

- [ ] **Step 1: Write failing `step_checks(5)`, `(6)`, `(7)`**: step 5 contains the AIM and SCIM options, consumer-access steps, channel table (UI, dashboard companion, Genie One, Conversation API, Teams, Slack) and the API best-practice list (poll 5 to 10 s, start new conversation per session, stop after about 10 minutes, only POST counts toward QPM); step 6 contains the `system.access.audit` query with `service_name = 'aibiGenie'`, the `system.query.history` filter on `query_source.genie_space_id`, the review cadence (weekly, fortnightly, monthly, quarterly) and rate limits 20 UI / 5 API per minute labelled published; step 7 contains waves 10/50/200 labelled field-recommended, a go/no-go table, rollback section, and promotion via bundles or the management API per the resolved claim.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Write steps 05 to 07** from Enterprise Phases 3 to 5, Pillars 5 and 6, the account-level onboarding guide, and the bundles migration doc (export, transform, load; idempotent deploy; service-principal permissions). SQL queries use env tokens.
- [ ] **Step 4: Run** → PASS; strip scan clean.
- [ ] **Step 5: Commit** `feat: add steps 05 to 07`

### Task 8: Developer track (Genie Code)

**Files:** Modify `index.html`, `assets/js/app.js`, `tests/guide_test.py`

**Interfaces:** Produces `<details id="developer-track">` with its own checklist stored under `genie-chk-dev-<i>` keys and excluded from `overall()`.

- [ ] **Step 1: Write failing tests**: track is collapsed by default; navigating to `#developer-track` expands it; ticking its checklist does not change the overall meter; `#step-9` loads without page errors; the track text cites only claims verified from public docs and contains no first-party internal references.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** the track from public Genie Code docs (what it is, where it runs, enabling and admin controls, guardrails, using it to author Agents and benchmarks), with `app.js` opening the `<details>` on matching hash.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: add Genie Code developer track`

### Task 9: Tracker, risk register, first wave

**Files:** Modify `index.html`, `assets/js/app.js` (reuse CSV download), `tests/guide_test.py`

- [ ] **Step 1: Write failing tests**: tracker has one row per lifecycle phase P1 to P5 with owner, due date, status select, notes; CSV download produces a file whose header is `Milestone,Owner,Due date,Status,Notes`; risk register has at least 8 rows each with likelihood, impact and mitigation; the "Top five ways rollouts stall" list from the Enterprise guide appears.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** by adapting the UC guide's tracker, risk and first-wave sections.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `feat: add tracker, risks and first wave`

### Task 10: PDF generation and staleness check

**Files:**
- Create: `tools/make-pdfs.py`, `assets/pdf/*.pdf`, `assets/pdf/MANIFEST.json`
- Modify: `index.html` (print-view anchors `data-pdf="<name>"` on source sections), `assets/css/style.css` (print rules), `tests/guide_test.py`

**Interfaces:**
- Produces: `python3 -I tools/make-pdfs.py` writing `rollout-plan.pdf`, `onboarding-checklist.pdf`, `benchmark-checklist.pdf`, `genie-one-agent-code.pdf`; `MANIFEST.json` mapping each file to `{"source": "<data-pdf name>", "sha256": "<hash of source section outerHTML>"}`.
- Consumes: shelf hrefs from Task 3.

- [ ] **Step 1: Write failing `pdf_checks`**: each shelf PDF href exists, size over 5 KB, starts with `%PDF`; MANIFEST hash equals the current hash of its source section; remove the `--allow-missing-pdf` flag.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** `make-pdfs.py` with Playwright `page.pdf()` on each `[data-pdf]` section (print media, A4, branded header with "Last verified" date), then writes the manifest.
- [ ] **Step 4: Run** the script, then the harness → PASS. Editing a source section without regenerating makes the harness FAIL (verify once by hand, then revert).
- [ ] **Step 5: Commit** `feat: add generated PDFs and staleness check`

### Task 11: Verification pass, README and release prep

**Files:** Create `README.md`; Modify `.htaccess` only if the Apache test requires it.

- [ ] **Step 1: Command verification.** Ask the user which Databricks profile to use (never auto-select). Run the Agent export/import and system-table queries from steps 04, 06 and 07 against it; mark each command "tested on <date>" or "untested" in the page.
- [ ] **Step 2: Full gates.** Run `python3 -I tests/guide_test.py`, `tests/axe.py <axe-dir>` (light and dark), `tests/contrast.py`, and the Apache 2.4 local test of `.htaccess` (headers present, CSP does not block the page, `.git` not exposed). All exit 0.
- [ ] **Step 3: Final strip scan** over the whole repo and the PDFs (`pdftotext` then grep) for customer names, person names, `go/`, Slack channels; zero hits outside rule text.
- [ ] **Step 4: Write `README.md`** (phases table, features, hosting, link to live Pages URL, licence note), matching the UC README layout.
- [ ] **Step 5: Commit** `docs: add README and verification results`, then ask the user to run `! git push origin main`. After the push, enable Pages from `main` root with `the repo owner's GitHub token` and confirm the live URL returns 200.
