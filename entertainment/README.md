# Entertainment

Three sub-features that let Fairy control your leisure time by voice: Spotify music playback, streaming site launching (Netflix + a secondary site), and Steam game recommendations. Each sub-feature lives in its own subfolder and is routed to from the main intent dispatcher.

---

## Music — `music/`

Controls Spotify playback via the **Spotipy** library (Spotify Web API, Authorization Code OAuth flow). Token is cached to `token_spotify.json` and refreshed automatically — no re-login after the first browser authorization.

### What it can do

- **Pause / resume / skip** — detected by keyword lists (`PAUSE_TRIGGERS`, `RESUME_TRIGGERS`, `SKIP_TRIGGERS`), whole-word matched to avoid false positives
- **Play by artist** — extracts an artist name from the voice query via regex, searches Spotify's catalog for the closest match, and starts playing that artist's full discography as a context URI
- **DJ mode** — pulls your top 20 most-listened tracks (medium-term), randomly samples 5, explicitly disables device shuffle first (so the ordered list actually plays), then queues them up. Falls back to DJ mode automatically when no specific intent is parsed

Every action triggers a **Groq-generated spoken line** — Fairy describes what she just did in one short, playful sentence rather than a canned phrase. A static fallback dict covers the case where Groq is unavailable.

**Tools/libraries:** `spotipy`, `groq`, `re`

---

## Streaming — `streaming/`

A two-step voice flow that launches either Netflix or a secondary streaming site (configurable via `STREAMING_OTHER_SITE_URL` in `.env`).

### Flow

1. Fairy asks: *"Netflix, or 'that site'?"*
2. User replies; intent is matched via keyword lists (`NETFLIX_TRIGGERS`, `OTHER_SITE_TRIGGERS`)

#### Netflix path
- Fairy asks what mood the user is in for tonight
- Launches the Netflix desktop app via its `.exe` shortcut path (`NETFLIX_EXE_PATH`)
- Passes the mood string + a personal hardcoded watchlist (defined in `brain/fairy_persona.py`) to **Groq**, which picks 1–2 matching titles and delivers a spoken recommendation in one line

#### "That site" path
- Attempts to open **ProtonVPN** (`PROTONVPN_EXE_PATH`) — located via `.env` path or `glob` fallback scan of the default install directory — so the VPN can be connected manually
- Opens **Firefox** (`FIREFOX_PATH`) to the configured `STREAMING_OTHER_SITE_URL`
- Fairy's spoken line acknowledges whether ProtonVPN opened successfully or needs manual attention

The secondary site URL is intentionally vague in the codebase — it's a configurable `.env` variable, not hardcoded, so it can be swapped to any target site.

**Tools/libraries:** `subprocess`, `os` (startfile), `groq`, `re`

---

## Gaming — `gaming/`

Connects to the **Steam Web API** to pull your owned game library and recommend something to play, with a confirmation-gated launch.

### Flow

1. Fetches your full owned game list (including free-to-play, app info, playtime data) via Steam's `GetOwnedGames` endpoint
2. **Recommendation logic** picks a game using one of three buckets (chosen randomly): recently played (active in the last 2 weeks, picks highest playtime), backlog (owned but under 60 minutes played, random pick), or fully random fallback
3. Fairy speaks a Groq-generated recommendation line naming the game and hinting at the reason
4. Asks for confirmation — "yes" triggers `os.startfile(f"steam://rungameid/{appid}")` to boot the game directly via Steam's URI protocol; "no" gets a playful decline line

**Tools/libraries:** `requests` (Steam API), `groq`, `os` (startfile), `re`

---

## Current scope

| Capability | Status |
|---|---|
| Spotify: pause, resume, skip | ✅ |
| Spotify: play by artist | ✅ |
| Spotify: DJ mode (top tracks, no shuffle) | ✅ |
| Netflix: mood-matched recommendation from personal watchlist | ✅ |
| Netflix: desktop app launcher | ✅ |
| Secondary streaming site: VPN + browser launch | ✅ |
| Steam: owned game library fetch | ✅ |
| Steam: smart recommendation (recent / backlog / random) | ✅ |
| Steam: voice-confirmed game launch | ✅ |
| Spotify: playlist/album playback by name | 🔲 Not yet — only artist context and top-track DJ mode |
| Netflix catalog search via RapidAPI | 🔲 Implemented but commented out — replaced by personal watchlist approach |
| Secondary site: automatic VPN connection (no manual step) | 🔲 Not yet — ProtonVPN has no official Windows CLI; requires manual connect after launch |
