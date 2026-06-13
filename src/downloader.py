import os
import logging
import requests
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

class INEDownloader:
    """Downloads bulk CSV tables from the INE jaxiT3 service."""
    
    BASE_URL = "https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/{table_id}.csv"
    
    # Standard table IDs for the Censo Anual de Población (Tract level)
    TABLES = {
        "studies": "66757",
        "activity": "66759",
        "occupation": "70097",
        "situation": "70099",
        "age": "69217"
    }

    def __init__(self, output_dir: str = "data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # Avoid basic blocks
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MedeaIndexScraper/1.0 (Research Project)"
        })

    def download_table(self, name: str, table_id: str) -> Path:
        """Downloads a specific table ID and saves it to the output directory."""
        url = self.BASE_URL.format(table_id=table_id)
        # We append _raw because these files contain all provinces; our parser filters them
        output_path = self.output_dir / f"{name}_raw.csv"
        
        logger.info(f"Downloading {name} data from {url}...")
        response = self.session.get(url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        logger.info(f"Saved {name} to {output_path}")
        return output_path

    def download_all(self) -> Dict[str, str]:
        """Downloads all the standard census tables required for the MEDEA index."""
        paths = {}
        for name, table_id in self.TABLES.items():
            path = self.download_table(name, table_id)
            paths[name] = str(path)
        return paths

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    downloader = INEDownloader()
    downloader.download_all()
