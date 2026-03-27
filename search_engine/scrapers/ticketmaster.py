import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
import logging

logger = logging.getLogger(__name__)

def scrape_ticketmaster(artist_name: str, timeout: int = 10):
    q = quote_plus(artist_name)
    url = f"https://www.ticketmaster.fr/search?q={q}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code != 200:
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        events = []
        # NOTE: selectors must be adapted to the real HTML structure of ticketmaster.fr
        for card in soup.select(".event-card, .search-result-item"):
            try:
                title = card.select_one(".event-title, .card-title")
                date = card.select_one(".event-date, .card-date")
                venue = card.select_one(".event-venue, .card-venue")
                link = card.select_one("a")
                events.append({
                    "nom": title.get_text(strip=True) if title else artist_name,
                    "date": date.get_text(strip=True) if date else "",
                    "lieu": venue.get_text(strip=True) if venue else "",
                    "source": link["href"] if link and link.has_attr("href") else url
                })
            except Exception:
                logger.exception("Failed to parse a ticketmaster card")
        return events
    except Exception as e:
        logger.exception("Scrape ticketmaster failed: %s", e)
        return []
