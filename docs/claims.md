# Claims register

Every volatile fact used in the guide has a row here. Steps cite the ID (`C-nn`) in an HTML comment next to the fact and show a "Last verified" date.

Status values: `verified` (confirmed against current public Databricks documentation or the cited public post), `unverified` (found only in internal source material, or not found in public docs; the guide says so in the text), `conflicting` (sources disagree and no resolution yet). A row marked "was conflicting" was resolved in favour of the cited public source.

Public documentation base: `https://docs.databricks.com/` (checked 17 Oct 2026).

| ID | Claim | Source | Status | Verified on |
|---|---|---|---|---|
| C-01 | Genie Agents were formerly Genie Spaces | docs `/genie-agents/` | verified | 2026-10-17 |
| C-02 | Genie One was previously Databricks One; it is the simplified UI for business users | docs `/genie-one/` | verified | 2026-10-17 |
| C-03 | Genie Code is the AI coding and data assistant for developers in the workspace; GA | docs `/genie-code/` | verified | 2026-10-17 |
| C-04 | An Agent supports up to 50 tables, views or metric views; start with five or fewer (was conflicting: internal sources and an older reference say 30). Creating Agents with 31 and 50 tables succeeded and 51 was rejected with "A space can have at most 50 tables" | docs `/genie-agents/set-up`, `/genie-agents/best-practices`; live test 17 Oct 2026 | verified | 2026-10-17 |
| C-05 | Up to 500 benchmark questions per Agent; 2 to 4 phrasings per question | docs `/genie-agents/monitor` | verified | 2026-10-17 |
| C-06 | 80% benchmark accuracy as the production gate | internal sources only; not in public docs | unverified | 2026-10-17 |
| C-07 | UI limit 20 questions per minute per workspace; Conversation API free tier 5 per minute | internal sources only; not found in public docs | unverified | 2026-10-17 |
| C-08 | Declarative Automation Bundles define Agents with the `genie_spaces` resource; direct deployment engine only; CLI 1.3.0 or later (was conflicting: one source said in development) | docs `/dev-tools/bundles/resources` | verified | 2026-10-17 |
| C-09 | Conversation API polling: every 1 to 5 seconds, limit to 10 minutes, exponential backoff up to one minute (was conflicting: internal sources say 5 to 10 seconds) | docs `/genie-agents/conversation-api` | verified | 2026-10-17 |
| C-10 | Instruction priority: SQL expressions first, example SQL second, text instructions last resort | docs `/genie-agents/best-practices` | verified | 2026-10-17 |
| C-11 | Limit of 100 instructions per Agent (each example SQL, each SQL function and the General instructions block count as one) | docs `/genie-agents/tune-quality` | verified | 2026-10-17 |
| C-12 | Agent ACLs: CAN MANAGE, CAN EDIT, CAN RUN, CAN VIEW (was conflicting: internal sources list three) | docs `/genie-agents/set-up` | verified | 2026-10-17 |
| C-13 | Compute uses the author's embedded credentials; data access is evaluated per user's own Unity Catalog identity; pro or serverless SQL warehouse required | docs `/genie-agents/set-up` | verified | 2026-10-17 |
| C-14 | Up to 200,000 conversations per Agent and 10,000 messages per conversation | docs `/genie-agents/set-up`, `/genie-agents/conversation-api` | verified | 2026-10-17 |
| C-15 | Genie cancels SQL queries running over 5 minutes and messages running over 30 minutes | docs `/genie-agents/troubleshooting` | verified | 2026-10-17 |
| C-16 | Audit log `service_name` is `aibiGenie`; actions include createSpace, getSpace, updateSpace, createConversation, createConversationMessage | docs audit log reference | verified | 2026-10-17 |
| C-17 | `system.query.history` identifies Genie queries through `query_source.genie_space_id` (4,101 rows in a day on the test workspace) | live query 17 Oct 2026 | verified | 2026-10-17 |
| C-18 | Genie Ontology is a semantic layer mapping business terms, metrics and relationships, governed through metric views, Pages and Domains; the Genie Code docs mark Genie Ontology as Public Preview | Databricks blog, "How to roll out Genie One", 28 Sep 2026; docs `/genie-code/features-capabilities` | verified | 2026-10-17 |
| C-19 | Genie One is GA at workspace and account level; Consumer access is the least-privileged entitlement for Genie One chat; account-only experience and Domains are Beta | docs `/genie-one/` | verified | 2026-10-17 |
| C-20 | Share to Account Users (embedded credentials) was a private preview that the account-level Genie path supersedes | internal sources only | unverified (omitted from guide) | 2026-10-17 |
| C-21 | Automatic Identity Management is GA and enabled by default for accounts created after 1 Aug 2025 | internal sources only | unverified | 2026-10-17 |
| C-22 | Customer-managed keys supported for Agents created after April 2025 | internal sources only | unverified | 2026-10-17 |
| C-23 | Embedding is by iframe; workspace admins configure allowed embedding surfaces; viewers need access to the Agent and its data | docs `/genie-agents/embed` | verified | 2026-10-17 |
| C-24 | A Genie app for Slack exists (@Genie mention, channel owners pin an Agent); Power Platform and Copilot Studio can call Genie Agents | docs `/genie-one/genie-slack/`, `/integrations/msft-power-platform/` | verified | 2026-10-17 |
| C-25 | Monitor tab shows questions, ratings, weekly digest; users answer "Is this correct?" with Yes, Fix it or Request review; CAN MANAGE sees feedback | docs `/genie-agents/monitor` | verified | 2026-10-17 |
| C-26 | Genie Code runs in notebooks, SQL editor, Lakeflow Pipelines Editor, AI/BI dashboards and a full-page experience; governed by the user's Unity Catalog permissions; admins manage budgets; a CLI exists | docs `/genie-code/`, `/genie-code/genie-code-cli` | verified | 2026-10-17 |
| C-27 | Knowledge Store holds descriptions, synonyms, join relationships, SQL expressions, prompt matching and column values; scoped to the Agent; trusted assets are parameterised queries and functions verified by an author | docs `/genie-agents/concepts` | verified | 2026-10-17 |
| C-28 | Genie chat was formerly called One Chat | internal sources only | unverified | 2026-10-17 |
| C-29 | Genie Code instructions: personal `.assistant_instructions.md` in the user's folder, workspace-wide `.assistant_workspace_instructions.md` (admins only, takes precedence), 20,000 character limit, `AGENTS.md` and `CLAUDE.md` files are picked up automatically | docs `/genie-code/instructions` | verified | 2026-10-17 |
| C-30 | Genie Code agent skills are folders containing `SKILL.md` with name and description frontmatter, in `Workspace/.assistant/skills/` or `/Users/<user>/.assistant/skills/`; loaded when relevant or by @mention; admins manage workspace skills | docs `/genie-code/skills` | verified | 2026-10-17 |
| C-31 | Genie Code needs partner-powered AI features enabled at account and workspace level for agentic capabilities (otherwise a Databricks-hosted model without them); it sends prompt, table and column names, descriptions, code, data samples and outputs within the user's permissions; account admins manage budgets | docs `/genie-code/` | verified | 2026-10-17 |
| C-32 | Genie Code has agent mode by default, chat, domain agents (data science, data engineering, document processing, dashboards, MLflow); Databricks recommends reviewing generated code before running it | docs `/genie-code/features-capabilities` | verified | 2026-10-17 |

## Open items for the text

- C-06, C-07, C-21, C-22, C-28: the guide states these as "from Databricks field guidance; not found in public documentation, confirm with the account team".
- C-20: left out of the guide.
- Wave sizes (10/50/200), review cadences, adoption targets and phase durations are field-recommended and labelled so; they are not claims about the product.

## Command verification log (17 Oct 2026)

Run on a Databricks test workspace (serverless SQL warehouse, Unity Catalog), using a scratch schema, scratch Agents and a scratch bundle that were all removed afterwards. Existing resources in the workspace were not touched.

| Guide block | Result |
|---|---|
| Step 01 documentation queries (`information_schema`) | Ran; listed tables and columns without comments |
| Step 02 table and column comments, `NOT NULL`, primary key | Ran |
| Step 02 grants | Ran with a user principal in place of a group, then reverted; syntax is identical for groups |
| Step 02 row filter and column mask | Ran; the filter returned only EMEA rows and the mask hid emails |
| Step 03 SQL expression and parameterised example SQL | Ran through the Statement Execution API with named parameters |
| Step 04 `genie-create-eval-run`, `genie-get-eval-run`, `genie-list-eval-results` | Ran with no request body; the run reached DONE, 2 of 2 correct |
| Step 05 `genie start-conversation` and `genie ask` | Ran; the conversation completed with correct SQL; `ask` answered through the Genie One chat |
| Step 06 audit query on `system.access.audit` | Ran; returned daily counts |
| Step 06 `system.query.history` filter on `query_source.genie_space_id` | Ran; the field exists |
| Step 07 `bundle generate genie-space` | Ran; wrote `src/<key>.geniespace.json` and `resources/<key>.genie_space.yml` |
| Step 07 `get-space --include-serialized-space` piped through `jq -r .serialized_space` | Ran; the file holds the inner definition |
| Step 07 bundle YAML, `bundle validate`, `bundle deploy` | Validated as written; deployed with a user principal in place of the group; the new Agent had its own ID and the full definition; `bundle destroy` removed it |
| `create-space` with the inner string; `update-space --serialized-space` | Ran |
| Agent table limit (31, 50 and 51 tables) | 31 and 50 accepted, 51 rejected |
