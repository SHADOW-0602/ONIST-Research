import asyncio
import logging
from crawl4ai import AsyncWebCrawler

logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self):
        pass

    async def scrape_url(self, url: str) -> str:
        """
        Uses Crawl4AI to asynchronously scrape and parse a webpage into markdown format.
        Used by the Layer 2 Footprint Agent to scrape PR Newswire, blogs, etc.
        """
        try:
            logger.info(f"Crawling URL: {url}")
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(
                    url=url,
                    # We can use LLM extraction or just raw markdown extraction
                    word_count_threshold=10,
                    bypass_cache=False,
                )
                if result.success:
                    return result.markdown
                else:
                    logger.error(f"Failed to crawl {url}: {result.error_message}")
                    return ""
        except Exception as e:
            logger.error(f"Crawl4AI exception for {url}: {str(e)}")
            return ""

scraper = WebScraper()