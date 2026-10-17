# Genie Deployment Guide: Design

Date: 2026-10-17
Repo: `jason-miles/genie-deployment-guide` (public)
Template: `jason-miles/UC-Migrations-Best-Practice-Guide` (local: `the sibling UC migration guide repo`)

## 1. Outcome

A public static guide for taking a Databricks Genie Agent (formerly Genie Space) from proof of concept to a governed, monitored, staged enterprise rollout. It distinguishes the three Genie products and keeps the same format, structure and interaction patterns as the UC migration guide.

Audience: Databricks SAs and DSAs using it as a delivery reference. Customers can read it, but it is not written as a customer deliverable.

Success criteria:
- A reader can tell within one screen which Genie product fits their need (step 00 chooser).
- A reader can follow steps 00 to 07 in order, copy commands, and tick a gate per step.
- Every volatile fact (names, limits, feature status) has a claims-register entry and a "Last verified" date.
- The shelf at the top offers up to six framed icon cards; PDF cards download on click, blog cards open in a new tab.
- No customer names, person names, `go/` links, internal Slack channels or internal document links appear anywhere in the repo.

## 2. The three products

| Product | What it is | Primary user | Where it appears in the guide |
|---|---|---|---|
| Genie One | Business-user front door: ask questions and get cited answers across governed data; account-level experience with consumer access | Business users | Step 05 (access and consumption) and step 07 (staged rollout) as the rollout channel |
| Genie Agent (formerly Genie Space) | Curated agent scoped to one business domain: tables, metric views, instructions, example SQL, benchmarks | Space authors, data teams | The spine: steps 01 to 07 |
| Genie Code | AI coding and data assistant inside the workspace | Developers, data practitioners | Parallel Developer track, outside the progress meter |

The guide also covers Genie Ontology (semantic layer built on Domains, Metric Views and Pages) in step 02, as it is the layer Genie One answers from.

Naming history is stated once in a glossary in step 00: Space to Agent, Databricks One to Genie One, One Chat to Genie chat. Source documents conflict on some of this; the claims register records the resolution.

## 3. Page structure

Single `index.html` with `assets/` (css, js, fonts, icons, pdf). No build step at runtime, no external network dependencies.

| Block | Content |
|---|---|
| Resource shelf | Up to six framed icon cards above step 00 |
| 00 Choose your path | Question-flow chooser (user, need, data shape) ending in a recommendation and a jump link; glossary; roles; credential-model chooser; deployment controls |
| 01 Discover and scope | Rank topics, good and bad topics, 20 to 50 questions, owner and RACI, success metrics (lifecycle P0) |
| 02 Data and governance | UC metadata, keys, tags, Metric Views, Ontology; quality gates; credential models; UC row filters and masks; access tiers; compliance tiers |
| 03 Build the Agent | Curation hierarchy, Knowledge Store, example SQL, sample questions, the two-week day-by-day plan (P1) |
| 04 Benchmark and validate | 80% gate, categories, technical then business-user validation (P1, P2) |
| 05 Access and consumption | Genie One onboarding (AIM or SCIM, consumer access), channels, Conversation API, Teams and Slack (P3) |
| 06 Monitor and operate | Monitor tab, audit and system tables, alerts, rate limits, feedback loop, review cadence (P4) |
| 07 Staged rollout and promotion | Waves 10/50/200, go/no-go, rollback, dev to prod via bundles or API (P5) |
| Developer track | Genie Code: where it fits, enabling it, guardrails, using it to build Agents; collapsible, own checklist |
| Tracker, risks, first wave | Milestone tracker with CSV download, risk register, first-wave guidance |

Each numbered step ends in a persisted gate that feeds the overall progress meter. The Developer track checklist persists separately and does not feed the meter.

## 4. Resource shelf

- Data lives in one array in `assets/js/app.js` (or an inline JSON block): `{type: "pdf" | "blog", title, href, icon, blurb}`. Maximum six entries; a test enforces the cap.
- Card: framed local SVG icon, title, type badge. Whole card is one link. Blog cards use `target="_blank" rel="noopener noreferrer"`. PDF cards use the `download` attribute and point to `assets/pdf/`.
- Accessible name states the type ("Download PDF: ..." or "Opens blog post: ...").
- Icons are original SVGs in the locked palette (Lava 600 #FF3621, Navy 900 #0B2026, Light #F9F7F4). No hotlinked or copied Databricks artwork.
- Initial cards: Genie One rollout playbook (blog, Databricks, 28 Sept 2026); rollout plan and tracker (PDF); technical onboarding checklist (PDF); benchmark checklist (PDF); Genie One vs Agent vs Code one-pager (PDF); one further public Databricks post found during research (blog).
- Layout: single row on wide screens, wraps on narrow, never more than two rows.

## 5. PDFs

- `tools/make-pdfs.py` renders PDFs with Playwright `page.pdf()` from dedicated print views of the real guide sections, so the PDFs and the page share one source.
- Output committed to `assets/pdf/`. The site has no runtime build step; the script is dev-time only.
- A test fails if a PDF is older than the source section it renders from (hash recorded in `assets/pdf/MANIFEST.json`).
- PDFs carry the same stripping rules as the page and a "Last verified" date.

## 6. Carried over from the UC guide

Environment panel with `{{var:default}}` tokens (catalog, schema, space ID, warehouse ID, group names, workspace URL); Ctrl+K search; sticky nav with scroll-spy and filter; reading progress bar; light and dark theme with manual toggle; print stylesheet; copy buttons; persisted gates and checklists; tracker CSV; local DM Sans and DM Mono; `.htaccess` with strict CSP; Apache-2.0 licence; `.nojekyll`; GitHub Pages from `main` root. Design context file `.databricks-impeccable.md` is adapted (audience, use case).

Design rules from the UC guide: no side-stripes, gates as checkboxes, WCAG AA, axe zero violations, `content-visibility:auto` not used (breaks anchor jumps).

## 7. Content rules

- Source: nine internal source documents (not published). The Enterprise Deployment Guide is the backbone; the two-week development guide feeds step 03; the field guide feeds step 01; the onboarding and rollout templates feed steps 04 and 07; the account-level onboarding guide feeds step 05; the bundles migration doc feeds step 07; the genie-ready and index docs are cross-checks.
- Strip: `go/` links, named people, internal Slack channels, Salesforce and internal-process references, customer names, internal doc links.
- Label every number as Databricks-published (for example 20 questions per minute in the UI, 5 on the API free tier, 30-table limit, 500 benchmarks per space, 80% accuracy guidance) or field-recommended (cadences, wave sizes, adoption targets). Published values are re-checked against current docs before publishing.
- Genie Code content comes from public documentation only, as the source documents do not cover it.
- Claims register `docs/claims.md`: one row per volatile fact with source, status (verified, unverified, conflicting) and date. Unverifiable facts are flagged in the text, not asserted. Known conflicts to resolve first: native bundle support for Agents (one source says GA from July 2026, another says in development); Space to Agent rename scope; Databricks One to Genie One naming; whether the Share-to-Account-Users preview is still current.
- Commands (CLI, SQL, API) are tested on a workspace the user names. No profile is auto-selected. Untested commands are marked as untested.

## 8. Testing

- Playwright harness (Python, `python3 -I`, local server on a free port; 8765 is taken by another process) modelled on the UC guide's 62 checks, extended with shelf checks: card count at most six, every `href` resolves (PDF files exist, blog URLs are well-formed https), PDF cards have `download`, blog cards have `rel`, keyboard focus order, accessible names.
- axe-core run: zero violations, light and dark.
- Contrast audit script reused from the UC guide.
- Apache 2.4 local test of `.htaccess`.
- Gate commit and push on the harness exit code, not on a `;` chain.

## 9. Delivery

Build in vertical slices, each reviewable:
1. Shelf, step 00 with chooser and glossary, harness, claims register skeleton.
2. Steps 01 to 04.
3. Steps 05 to 07, Developer track, tracker, risks, first wave.
4. PDFs, accessibility and contrast pass, README, push.

The claims verification (current docs) runs in parallel with repo setup and template copy.

Push uses SSH (`origin` is `git@github.com:jason-miles/...`). The user pushes with `! git push origin main`. Pages API calls use `the repo owner's GitHub token`. Commits end with `Co-authored-by: Isaac <no-reply@databricks.com>`.

## 10. Out of scope

- Customer-specific content or branded variants.
- Full Genie One and Genie Code deployment tracks (the guide is Agent-led).
- Hosting changes beyond GitHub Pages and the `.htaccess` file.
- Any automation that creates or modifies Genie Agents in a workspace (the guide documents the export and import path; it does not ship tooling).
