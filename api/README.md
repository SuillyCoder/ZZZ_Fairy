# Web Info — Weather & News

Fetches live, real-world information so Fairy can answer questions like "what's the weather" or "what's happening in the news" with current data rather than stale training knowledge.

## Weather — `weather.py`

`get_weather()` pulls live conditions for Cebu City from **OpenWeatherMap**.

- Returns a spoken-friendly summary: description, temperature (Celsius), "feels like," humidity, and wind speed (converted from m/s to km/h)
- Handles specific failure modes distinctly — no internet, timeout, invalid API key (401), city not found (404), and unexpected response shapes — so Fairy gives a useful spoken explanation instead of a generic error

**Tools/libraries:** `requests`, OpenWeatherMap API

## News — `news.py` + `scraper.py`

`get_news()` returns the top local headlines, with a two-tier fallback strategy: try a real news API first, and only fall back to scraping if that comes up empty.

- **Primary source:** NewsAPI, filtered to Cebu-related, English-language, most-recent articles
- **Fallback:** if NewsAPI returns nothing (rate limit, no results, etc.), falls through to `scraper.py`, which scrapes headlines directly from SunStar Cebu, then Cebu Daily News (via Inquirer) if SunStar also comes up empty
- `scraper.py` also includes a PAGASA weather-bulletin scraper as a bonus/secondary source, separate from the OpenWeatherMap integration above

**Tools/libraries:** `requests`, `BeautifulSoup` (`bs4`), NewsAPI

## Current scope

| Capability | Status |
|---|---|
| Live weather for Cebu City | ✅ |
| Local news via NewsAPI | ✅ |
| Scraper fallback (SunStar, Cebu Daily News) | ✅ |
| PAGASA weather bulletin scraping | ✅ (bonus, not yet wired into the main weather intent) |
| Configurable city/region (beyond Cebu) | 🔲 Not yet — currently hardcoded to Cebu City, PH |
