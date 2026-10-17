# Genie Deployment Guide: From Proof of Concept to Enterprise Rollout

A step-by-step guide for deploying Databricks Genie Agents (formerly Genie Spaces) at enterprise scale, published as a static HTML site. It also explains how Genie One and Genie Code fit alongside Agents.

**Read the guide: https://jason-miles.github.io/genie-deployment-guide/**

To run it locally, open `index.html` or serve the repo root with any web server.

## The three Genie products

| Product | What it is | Where it appears |
|---|---|---|
| Genie One | Simplified UI for business users | Steps 05 and 07, as the access and rollout channel |
| Genie Agent (formerly Genie Space) | Curated, per-domain agent | Steps 01 to 07, the spine of the guide |
| Genie Code | AI coding and data assistant for developers | Developer track, outside the step gates |

## Steps

| # | Step | Focus |
|---|------|-------|
| 00 | Choose your path | Product chooser, glossary, credential patterns, roles, controls |
| 01 | Discover and scope | Topic ranking, stakeholders, questions, success metrics |
| 02 | Data and governance | Unity Catalog metadata, Metric Views, credentials, grants, filters, masks, compliance tiers |
| 03 | Build the Agent | Curation hierarchy, Knowledge Store, example SQL, the two-week plan, troubleshooting |
| 04 | Benchmark and validate | Benchmark suite, accuracy gate, technical and business validation |
| 05 | Access and consumption | Identity provisioning, Consumer access, channels, Conversation API |
| 06 | Monitor and operate | Monitor tab, audit and system tables, alerts, limits, review cadence |
| 07 | Staged rollout and promotion | Waves, go/no-go, rollback, promotion with bundles |
| GC | Genie Code track | Enabling, governing and using Genie Code |
| + | Tracker, risks and first wave | Milestone tracker with CSV download, risk register, first-wave guidance |

## Features

- **Resource shelf:** framed icon cards at the top link to blog posts and download PDFs (rollout plan, onboarding checklist, benchmark checklist, product comparison).
- **Your environment panel:** enter catalog, schema, table, Agent ID, warehouse and group once; every code sample rewrites live.
- **Search palette:** Ctrl/Cmd+K searches all content.
- **Progress:** persisted step gates and checklists feed one overall meter; the Genie Code checklist is tracked separately.
- Light and dark themes, print stylesheet, copy buttons on every code block.
- Every code block is labelled with its test status. Commands have not yet been run against a workspace.

## Accuracy and sources

Product facts are checked against public Databricks documentation and listed in [`docs/claims.md`](docs/claims.md) with a status and date. Figures not found in public documentation (for example the 80% accuracy gate and the question-per-minute limits) are labelled "field guidance" in the text.

## Hosting

- **GitHub Pages:** Settings, Pages, deploy from the default branch root. `.nojekyll` is included.
- **Apache httpd:** `.htaccess` enables compression, caching and security headers (needs `mod_deflate`, `mod_expires`, `mod_headers`).

## Development

No build step at runtime. Dev-time tools:

```bash
python3 -I tests/guide_test.py          # Playwright checks (shelf, steps, tracker, PDFs, accessibility basics)
python3 -I tests/apache_test.py         # serves the repo with the system Apache 2.4
python3 -I tools/make-pdfs.py           # regenerate assets/pdf after editing a data-pdf section
```

`tests/axe.py <url> [axe.min.js]` runs axe-core and `tests/contrast.py <url>` checks colour contrast. The harness fails if a PDF is older than the page sections it was rendered from.

## Licence

Apache-2.0. See `LICENSE`.
