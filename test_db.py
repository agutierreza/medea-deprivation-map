import os
import logging
from src.db import DatabaseManager
from src.scraper import BaseScraper

logging.basicConfig(level=logging.DEBUG)

def main():
    # Ensure data dir exists
    os.makedirs("data", exist_ok=True)
    
    # Test Database
    db_path = "data/malaga_census.db"
    db = DatabaseManager(db_path)
    
    tract_id = "2906701001" # Málaga tract example
    var_group = "unemployment"
    
    # Insert dummy data
    db.insert_data(tract_id, var_group, {"status": "success", "data": [1, 2, 3]})
    print(f"Is downloaded? {db.is_downloaded(tract_id, var_group)}")
    print(f"Data: {db.get_data(tract_id, var_group)}")
    
    # Test Scraper
    scraper = BaseScraper(delay=1.5)
    
    print("Testing scraper throttling... (should wait 1.5s between requests)")
    # We test with a safe endpoint (e.g., httpbin) just to test throttling
    for i in range(2):
        scraper._throttled_request("GET", "https://httpbin.org/get")

if __name__ == "__main__":
    main()
