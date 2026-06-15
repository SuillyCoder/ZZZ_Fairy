import requests
from bs4 import BeautifulSoup

#Headers to bypass blocking without proper URL headers
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

REQUEST_TIMEOUT = 8

def fetch_headlines(url: str, tag: str, attrs: dict, limit: int = 5) -> list[str]:
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT) #Get request the response data
        response.raise_for_status() #Throw exception if HTTP status is 4XX or 5XX
        soup = BeautifulSoup(response.text, "html.parser")
        elements = soup.find_all(tag, attrs)

        headlines = []
        for el in elements:
            text = el.get_text(strip=True)   # get_text() pulls just the human-readable text
            if text and len(text) > 10:      # Skip tiny/empty strings
                headlines.append(text)
            if len(headlines) >= limit:
                break
 
        return headlines

    #Exception handling
    except requests.exceptions.ConnectionError:
        print(f"[Scraper Error]: Couldn't connect to {url}")
        return []
 
    except requests.exceptions.Timeout:
        print(f"[Scraper Error]: Timed out on {url}")
        return []
 
    except requests.exceptions.HTTPError as e:
        print(f"[Scraper Error]: HTTP {e.response.status_code} on {url}")
        return []
 
    except Exception as e:
        print(f"[Scraper Error]: {e}")
        return []
    
#======= NEWS OUTLET SCRAPING SECTION =======#
    
#SunStar
def scrape_sunstar(limit: int = 5) -> list[str]:
     print("[Scraper]: Fetching SunStar Cebu headlines...")
     return fetch_headlines(
        url="https://www.sunstar.com.ph/cebu",
        tag="h2",                           # Headline tag on SunStar
        attrs={"class": "article__title"},  # CSS class — may need updating if site redesigns
        limit=limit,
    )

#CDN
def scrape_cdn(limit: int = 5) -> list[str]:
    print("[Scraper]: Fetching CDN headlines...")
    return fetch_headlines(
        url="https://cebudailynews.inquirer.net/",
        tag="h2",
        attrs={"class": "entry-title"},   # Inquirer network standard class
        limit=limit,
    )

#PAGASA (bonus)
def scrape_pagasa_bulletin() -> str: 
    print("[Scraper]: Fetching PAGASA bulletin for Cebu...")
    try:
        response = requests.get( #GET request for Pagasa response data
            "https://www.pagasa.dost.gov.ph/weather",
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        for p in paragraphs:
            text = p.get_text(strip=True)
            if "Cebu" in text and len(text) > 30:
                return text  # Return the first paragraph mentioning Cebu
 
        return ""  # Nothing found
 
    except Exception as e:
        print(f"[PAGASA Scraper Error]: {e}")
        return ""