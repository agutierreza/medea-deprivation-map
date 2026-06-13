import os
import logging
import requests
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

class INEDownloader:
    """Downloads bulk CSV tables from the INE jaxiT3 service."""
    
    BASE_URL = "https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/{table_id}.csv"
    
    def __init__(self, output_dir: str = "data", province_code: str = "29"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.province_code = str(province_code).zfill(2)
        
        # Load registry
        registry_path = self.output_dir / "ine_table_registry.json"
        if not registry_path.exists():
            raise FileNotFoundError(f"Registry file not found at {registry_path}. Run build_table_registry.py first.")
            
        import json
        with open(registry_path, "r", encoding="utf-8") as f:
            registry = json.load(f)
            
        if self.province_code not in registry:
            raise ValueError(f"Province code {self.province_code} not found in registry.")
            
        self.TABLES = registry[self.province_code]
        
        # Avoid basic blocks
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MedeaIndexScraper/1.0 (Research Project)"
        })

    def download_table(self, name: str, table_id: str) -> Path:
        """Downloads a specific table ID and saves it to the output directory."""
        url = self.BASE_URL.format(table_id=table_id)
        # Use province_code in the filename instead of _raw
        output_path = self.output_dir / f"{name}_{self.province_code}.csv"
        
        logger.info(f"Downloading {name} data for province {self.province_code} from {url}...")
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
    # Example usage for Almería
    downloader = INEDownloader(province_code="04")
    downloader.download_all()
