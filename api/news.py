import requests, sys, os
from api.scraper import scrape_sunstar, scrape_cdn   

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NEWS_API_KEY

NEWS_BASE_URL = "https://newsapi.org/v2/everything"
HEADLINE_COUNT = 3    # How many headlines to read aloud (keep it short for voice)

def get_news() -> str: 
    headlines = _fetch_from_newsapi()



#===== Helper Functions====#

def _fetch_from_newsapi():
    try:
        params = {
            "q": "Cebu",               # Keyword search — filters for Cebu-related content
            "language": "en",          # English articles only
            "sortBy": "publishedAt",   # Most recent first
            "pageSize": HEADLINE_COUNT,
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
        return headlines[:HEADLINE_COUNT]
        # [Data] ===>> [Articles] ===>> [Title]
    
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

#====== Scraper Fallback =======#

def _fetch_from_scraper() -> list[str]:
    headlines = scrape_sunstar() #Scrape the headlines from CDN first
    if not headlines: 
        headlines = scrape_cdn() #Try from CDN instead
    return headlines[:HEADLINE_COUNT]





 