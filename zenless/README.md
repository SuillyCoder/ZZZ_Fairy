# Zenless Zone Zero Integration

The "bonus" feature that ties the whole project's theme together: Fairy can check your actual *Zenless Zone Zero* account — status, characters, banners, and news — sourced from third-party community APIs rather than an official public API (HoYoverse doesn't provide one for this kind of access).

## Account status — `get_account_status()`

Connects to **HoYoLAB** via the `genshin.py` library (which, despite the name, supports multiple HoYoverse games including ZZZ) using session cookies (`ltuid_v2`/`ltoken_v2`) rather than a username/password login.

- Reports current battery charge (the game's energy/stamina resource), daily engagement progress, and weekly task progress
- Validated once at boot (`validate_hoyolab_cookies()`) so Fairy knows upfront whether the session is alive or needs refreshing, rather than failing silently mid-conversation

## Character showcase — `get_character_showcase()`

Pulls your public profile showcase from **Enka.Network** (a community-run API that reads public in-game profile data without needing your account cookies).

- Cross-references character IDs against a name lookup table fetched from Enka's GitHub-hosted data files, cached locally for 7 days since the agent roster only changes per game patch
- Reports Inter-Knot level, agent count, and top 3 agents by level

## Banners & news — `get_banner_status()` / `get_latest_zenless_news()`

Sourced from the **Ennead API**, a community-maintained replacement for official ZZZ news/banner data (adopted after Reddit's 2025 API policy changes made the original planned approach impractical).

- `get_banner_status()` — lists currently active character banners and days remaining
- `get_latest_zenless_news()` — fetches recent official notice titles and asks **Groq** to summarize them into a short spoken blurb (the LLM only summarizes the titles it's given — it's instructed not to invent details beyond them)

## Proactive nudges — `check_zzz_nudges()` / `start_zzz_monitor()`

Runs on a background daemon thread (default: hourly) and proactively speaks up when:

- Energy/battery crosses 90% of max capacity (so it doesn't go to waste capped out) — fires once per threshold crossing, resets once spent back down
- A new character banner goes live since the last check

**Tools/libraries:** `genshin` (HoYoLAB client), `requests` (Enka.Network, Ennead API), `groq`, `threading`, `asyncio`

## Current scope

| Capability | Status |
|---|---|
| HoYoLAB account status (energy, engagement, weekly tasks) | ✅ |
| Public character showcase via Enka.Network | ✅ |
| Banner status via Ennead API | ✅ |
| News/notice summarization via Groq | ✅ |
| Proactive energy-cap and new-banner nudges | ✅ |
| Auto-farming / in-game automation | 🔲 Not planned — out of scope (would require game-client automation, not just data fetching) |
