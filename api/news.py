import requests, sys, os, random
from groq import Groq
from api.scraper import scrape_sunstar, scrape_cdn

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NEWS_API_KEY, GROQ_MODEL, FAIRY_GROQ_API_KEY

groq_client = Groq(api_key=FAIRY_GROQ_API_KEY)

NEWS_BASE_URL = "https://newsapi.org/v2/everything"
HEADLINE_COUNT = 3        # How many headlines to read aloud (keep it short for voice)
CANDIDATE_POOL_SIZE = 15  # Larger pool to randomize from, so repeat asks don't return the same 3
SEARCH_RESULT_CAP = 3  # Max articles to surface for a topic search

def get_news() -> str:
    headlines = _fetch_from_newsapi()
    if not headlines:
        print("[News]: NewsAPI returned no results. Trying scrapers...")
        headlines = _fetch_from_scraper()

    if not headlines:
        return ""

    # Deterministic fallback built first, from the real headlines, before touching Groq.
    fallback_spoken = _build_fallback_response(headlines)

    try:
        spoken = _generate_dynamic_response(headlines)
        print(f"[News]: {spoken}")
        return spoken
    except Exception as e:
        print(f"[News - Groq Error]: {e}")
        print(f"[News]: {fallback_spoken}")
        return fallback_spoken

#===== Helper Functions====#

def search_news(topic: str) -> str:
    if not topic or not topic.strip():
        return "I'm not sure what you'd like me to search for, Master. Could you be more specific?"

    print(f"[News Search]: Searching for '{topic}'...")

    try:
        params = {
            "q": topic,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": SEARCH_RESULT_CAP,
            "apiKey": NEWS_API_KEY,
        }
        response = requests.get(NEWS_BASE_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        articles = [
            a for a in data.get("articles", [])
            if a.get("title") and "[Removed]" not in a["title"]
        ]
    except requests.exceptions.ConnectionError:
        return "I couldn't reach the news service, Master. Check your connection."
    except requests.exceptions.Timeout:
        return "The news search timed out, Master. Try again in a moment."
    except requests.exceptions.HTTPError as e:
        return f"News search hit an error, Master. Status {e.response.status_code}."
    except Exception as e:
        print(f"[News Search Error]: {e}")
        return "Something went wrong while searching the news, Master."

    # Let Groq synthesize — passing real article data only, no hallucination allowed
    try:
        spoken = _generate_search_response(topic, articles)
        print(f"[News Search]: {spoken}")
        return spoken
    except Exception as e:
        print(f"[News Search - Groq Error]: {e}")
        # Deterministic fallback if Groq fails
        if not articles:
            return f"I couldn't find anything on '{topic}' in recent news, Master."
        titles = "; ".join(a["title"] for a in articles)
        return f"Here's what I found on {topic}: {titles}"

def extract_news_topic(text: str) -> str:
    import re
    fillers = [
        r"^(is there |do you have |got |any |anything |something |tell me |what about |how about |search for |look up |find |what('?s| is) (the |new |latest )?(news |update |story |stories |info |information )?about |news (about |on )|anything (on |about ))",
    ]
    cleaned = text.strip().lower()
    for pattern in fillers:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = cleaned.rstrip("?.,!")
    return cleaned.strip()

# ===== Internal Helpers ====== #

def _fetch_from_newsapi():
    try:
        params = {
            "q": "Cebu",               # Keyword search — filters for Cebu-related content
            "language": "en",          # English articles only
            "sortBy": "publishedAt",   # Most recent first
            "pageSize": CANDIDATE_POOL_SIZE,   # Pull a larger pool — was mistakenly HEADLINE_COUNT (3), which meant random.sample() had nothing to actually vary
            "apiKey": NEWS_API_KEY,
        }

        response = requests.get(NEWS_BASE_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        articles = data.get("articles", []) #Passes the articles from the mass-extracted data
        headlines = [ #Extracts the relevant headlines from the extracted articles
            a["title"]
            for a in articles
            if a.get("title") and "[Removed]" not in a["title"]
        ]
        return random.sample(headlines, min(HEADLINE_COUNT, len(headlines)))
        # [Data] ===>> [Articles] ===>> [Title] ===>> [Random subset]

    #Exception Handling
    except requests.exceptions.ConnectionError:
        print("[News Error]: No internet connection.")
        return []

    except requests.exceptions.Timeout:
        print("[News Error]: Request timed out.")
        return []

    except requests.exceptions.HTTPError as e:
        print(f"[News Error]: HTTP {e.response.status_code}")
        return []

    except Exception as e:
        print(f"[News Error]: {e}")
        return []


def _build_fallback_response(headlines: list[str]) -> str:
    """The original, deterministic news template. Used if Groq fails."""
    intro = f"Here are the top {len(headlines)} headlines from Cebu:"
    items = " ... ".join([f"Headline {i+1}: {h}" for i, h in enumerate(headlines)])
    return f"{intro} {items}"


def _generate_dynamic_response(headlines: list[str]) -> str:
    headline_list = "\n".join(f"- {h}" for h in headlines)

    prompt = f"""You are Fairy, a voice assistant. Deliver the following real Cebu news
headlines to the user in a short, natural, spoken-style summary — like you're
casually catching them up, not reading a rigid list.

REAL HEADLINES (use these exact stories — do not invent, omit, or alter their
factual content; you may only rephrase HOW you introduce/transition between them):
{headline_list}

Instructions:
- Mention all {len(headlines)} headlines, each as its own short beat.
- No markdown, no bullet points, no numbered list — this will be spoken aloud.
- Keep it brief: a sentence or two of intro, then the headlines woven in naturally.
- Stay in character: efficient, a little playful, address the user as "Master" or
  similar, the way Fairy normally talks.
- Do not add any news content that wasn't in the list above."""

    completion = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200,
        temperature=0.5,
    )
    return completion.choices[0].message.content.strip()

def _generate_search_response(topic: str, articles: list[dict]) -> str:
    if not articles:
        article_block = "No articles found."
    else:
        lines = []
        for a in articles:
            title = a.get("title", "No title")
            source = a.get("source", {}).get("name", "Unknown source")
            desc = a.get("description") or ""
            lines.append(f"- [{source}] {title}: {desc}")
        article_block = "\n".join(lines)

    prompt = f"""You are Fairy, a voice assistant. The user asked about: "{topic}"

Here are the ONLY real news results found. Do not invent, add, or imply any
information that is not explicitly present below:

SEARCH RESULTS:
{article_block}

Instructions:
- If no articles were found, tell the user honestly that you couldn't find recent
  coverage on that topic — do NOT make up stories or say "I found..." if you didn't.
- If articles were found, give a brief spoken summary of what the results say —
  one or two natural sentences, no bullet points or markdown.
- Stay in character as Fairy: efficient, slightly playful, address the user as "Master".
- Never fabricate quotes, facts, names, or details not present in the results above."""

    completion = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=180,
        temperature=0.3,   # Lower temp for factual synthesis — less creative drift
    )
    return completion.choices[0].message.content.strip()

#====== Scraper Fallback =======#

def _fetch_from_scraper() -> list[str]:
    headlines = scrape_sunstar() #Scrape the headlines from CDN first
    if not headlines:
        headlines = scrape_cdn() #Try from CDN instead
    return headlines[:HEADLINE_COUNT]