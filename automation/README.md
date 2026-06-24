# Automation

The largest feature set — everything where Fairy does real work on your behalf: checking accounts, crunching numbers, and assisting with code.

## Email — `email_handler.py`

Checks and manages your Gmail inbox via the **Gmail API**.

- `get_unread_emails()` — fetches up to 7 unread inbox messages, returns a spoken summary of sender + subject per email (sender names are cleaned up from raw `"Name" <email>` format)
- `mark_all_fetched_as_read()` — batch-removes the `UNREAD` label from the same fetch
- OAuth flow runs once (opens a browser to authorize), then reuses a saved token on subsequent runs — no repeated logins

**Tools/libraries:** `google-auth`, `google-auth-oauthlib`, `google-api-python-client` (Gmail API v1)

## Discord — `discord_handler.py`

Checks recent activity across all text channels in a single configured Discord server.

- `fetch_recent_messages()` — async, connects via `discord.py`, pulls the last 3 messages per text channel, skips bot messages
- Groups results by channel for the spoken summary, and gracefully skips channels the bot doesn't have permission to read rather than failing the whole request
- Handles invalid token and missing server-ID configuration with specific spoken errors

**Tools/libraries:** `discord.py` (async)

## Finance — `finance.py`

The most complex module — reads a Google Sheets expense tracker and answers natural-language questions about spending.

- `load_all_sheets()` — pulls every tab from a configured spreadsheet via `gspread`, auto-detects header rows, separates **monthly tabs** (named after calendar months) from **trip tabs** (e.g. "JAPAN_TRIP_1"), and auto-converts trip currency to PHP using a detected exchange rate embedded in the sheet
- `classify_finance_sub_intent()` — uses **Groq** to parse the voice query into a structured sub-intent (monthly summary, category breakdown, recommendations, plotting, trip summary, etc.) plus any mentioned month/category/trip
- Routing then splits between three different engines depending on what's being asked:
  - **Pandas** — straightforward aggregation (`summarize_month`, `all_time_summary`, `category_summary`, `trip_summary`)
  - **Groq** — natural-language financial advice/recommendations (`groq_recommendations`) — language work, not math
  - **Ollama (lfm2.5, local)** — heavier statistical reasoning like trends, projections, and anomalies (`lfm25_heavy_analysis`) — kept local since it's number-crunching, not persona work
- Three plot types via `matplotlib`: monthly totals (bar chart with average line), category breakdown (pie chart), and a spending timeline (daily + cumulative line chart) — each saved to `plots/` and shown in a native window

**Tools/libraries:** `gspread`, `pandas`, `matplotlib` (TkAgg backend), `groq`, local Ollama via `requests`, Google OAuth

## Code Assistant — `code_assistant.py`

A self-referential feature: Fairy can review, comment, and help commit changes to her *own* codebase (or any other local file/repo) using a mix of local and cloud models.

- `review_code()` — chunks a file by function/class boundaries (via `ast`, falling back to fixed-line chunking for non-Python files), sends each chunk to local **Ollama (lfm2.5)** for a bug/style review
- `generate_commented_version()` — same chunking approach, asks lfm2.5 to add inline comments without altering logic, saves a `.commented_preview.py` file and a `difflib` diff rather than overwriting anything directly
- `apply_commented_version()` / `discard_commented_version()` — confirmation-gated: nothing gets applied until the user explicitly says so, and applying always backs up the original first
- `generate_commit_message()` / `confirm_commit()` — reads the staged (or unstaged, with a warning) git diff, asks lfm2.5 to draft a conventional-commit-style message, and only runs `git commit` after explicit user confirmation
- `diagnose_error()` — sends an error message + relevant source to **Groq** for a root-cause-and-fix diagnosis (cloud model, since this benefits from broader reasoning over a focused chunk)
- `suggest_refactor()` — flags functions/files over a line-count threshold and asks Groq for a refactor approach (description only — it doesn't rewrite the file itself)

**Tools/libraries:** `ast`, `difflib`, `shutil`, `subprocess` (git), local Ollama via `requests`, `groq`

## Current scope

| Capability | Status |
|---|---|
| Gmail unread check + mark-as-read | ✅ |
| Discord recent-message check (single guild) | ✅ |
| Expense tracker: summaries, breakdowns, trends, recommendations | ✅ |
| Expense plotting (monthly, category, timeline) | ✅ |
| AI code review, commenting, commit messages, error diagnosis, refactor suggestions | ✅ |
| Multi-server Discord support | 🔲 Not yet — single guild, auto-discovered channels only |
