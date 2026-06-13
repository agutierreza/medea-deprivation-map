import time
import logging
from typing import Optional, Dict, Any
import requests

logger = logging.getLogger(__name__)

class BaseScraper:
    """Base scraper class that ensures requests are throttled to avoid API bans."""
    
    def __init__(self, delay: float = 2.0):
        self.delay = delay
        self.session = requests.Session()
        # Ensure we send appropriate headers to avoid simple bans
        self.session.headers.update({
            "User-Agent": "MedeaIndexScraper/1.0 (Research Project)",
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        self.last_request_time = 0.0

    def _throttled_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make an HTTP request ensuring at least `self.delay` seconds have passed
        since the last request.
        """
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.delay:
            sleep_time = self.delay - time_since_last
            logger.debug(f"Throttling: sleeping for {sleep_time:.2f} seconds.")
            time.sleep(sleep_time)

        logger.info(f"Making {method.upper()} request to {url}")
        response = self.session.request(method, url, **kwargs)
        
        self.last_request_time = time.time()
        return response

    def post(self, url: str, payload: Dict[str, Any], retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        Make a POST request with retry logic for 5xx and 429 status codes.
        """
        for attempt in range(retries):
            try:
                response = self._throttled_request("POST", url, json=payload)
                
                if response.status_code == 200:
                    return response.json()
                    
                if response.status_code in (429, 500, 502, 503, 504):
                    wait = (attempt + 1) * self.delay * 2
                    logger.warning(f"Got status {response.status_code}. Retrying in {wait}s...")
                    time.sleep(wait)
                    continue
                    
                logger.error(f"Failed request to {url}. Status: {response.status_code}, Response: {response.text}")
                return None
                
            except requests.RequestException as e:
                wait = (attempt + 1) * self.delay * 2
                logger.warning(f"Request exception: {e}. Retrying in {wait}s...")
                time.sleep(wait)
                
        logger.error(f"Max retries reached for {url}")
        return None
