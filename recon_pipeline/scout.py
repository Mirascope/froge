# scout.py
import asyncio
import feedparser
import httpx
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, HttpUrl
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Headline(BaseModel):
    """Represents a single fetched headline."""
    source: str
    title: str
    url: HttpUrl
    summary: Optional[str] = None

async def fetch_headlines(source_name: str, rss_url: str, limit: int = 5) -> List[Headline]:
    """
    Fetches headlines from a given RSS feed URL.

    Args:
        source_name: A short name for the news source (e.g., "BBC News").
        rss_url: The URL of the RSS feed.
        limit: The maximum number of headlines to fetch.

    Returns:
        A list of Headline objects.
    """
    headlines = []
    logging.info(f"Scout fetching headlines from {source_name} ({rss_url})...")
    try:
        # Use httpx for async request and feedparser to parse
        # Enable follow_redirects=True
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(rss_url, timeout=10.0)
            response.raise_for_status() # Raise an exception for bad status codes

        feed = feedparser.parse(response.text)

        for entry in feed.entries[:limit]:
            try:
                headline = Headline(
                    source=source_name,
                    title=entry.title,
                    url=entry.link,
                    # Attempt to get summary, handle missing attribute gracefully
                    summary=getattr(entry, 'summary', None) 
                )
                headlines.append(headline)
            except Exception as e:
                logging.warning(f"Could not parse entry from {source_name}: {entry.title}. Error: {e}")

    except httpx.RequestError as e:
        logging.error(f"HTTP error fetching {source_name} feed: {e}")
    except httpx.HTTPStatusError as e: # Catch status errors specifically
         logging.error(f"HTTP status error fetching {source_name} feed for url {e.request.url}: {e.response.status_code} - {e.response.reason_phrase}")
    except Exception as e:
        logging.error(f"Error processing {source_name} feed ({rss_url}): {e}")

    logging.info(f"Scout finished fetching {len(headlines)} headlines from {source_name}.")
    return headlines

# Example usage for standalone testing
async def main():
    test_url = "http://feeds.bbci.co.uk/news/rss.xml" # Example RSS feed
    source_name = "BBC News"
    fetched = await fetch_headlines(source_name, test_url)
    if fetched:
        print(f"\n--- Fetched Headlines ({source_name}) ---")
        for h in fetched:
            print(f"- {h.title} ({h.url})")
    else:
        print(f"No headlines fetched from {source_name}.")

if __name__ == "__main__":
    asyncio.run(main()) 
