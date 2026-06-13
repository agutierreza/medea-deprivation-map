import logging
import pandas as pd
from pathlib import Path
from src.parser import LocalDataParser
from src.medea import MedeaCalculator
from src.db import DatabaseManager

# Setup basic logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

import argparse
from src.downloader import INEDownloader

def run_pipeline(
    db_path: str,
    studies_path: str,
    activity_path: str,
    occupation_path: str
):
    logger.info("Initializing database manager...")
    db = DatabaseManager(db_path)
    
    logger.info("Initializing local data parser...")
    parser = LocalDataParser(
        studies_path=studies_path,
        activity_path=activity_path,
        occupation_path=occupation_path
    )
    
    logger.info("Parsing census CSV files...")
    tracts_data = list(parser.yield_tract_data())
    logger.info(f"Successfully parsed data for {len(tracts_data)} census tracts.")
    
    if not tracts_data:
        logger.error("No tracts parsed. Aborting.")
        return
        
    logger.info("Calculating MEDEA percentages for each tract...")
    percentages_list = []
    for tract in tracts_data:
        pcts = MedeaCalculator.calculate_percentages(tract)
        percentages_list.append(pcts)
        
    # Convert to DataFrame for PCA
    df_pcts = pd.DataFrame(percentages_list)
    
    logger.info("Running PCA to compute final MEDEA score...")
    df_results = MedeaCalculator.calculate_pca_index(df_pcts)
    
    logger.info("Saving results to the database...")
    saved_count = 0
    for _, row in df_results.iterrows():
        # Convert row to dict, replace NaN with None for SQLite
        row_dict = row.where(pd.notna(row), None).to_dict()
        db.insert_medea_results(row_dict["tract_id"], row_dict)
        saved_count += 1
        
    logger.info(f"Pipeline complete! {saved_count} tract results saved to {db_path}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the MEDEA pipeline for a specific province.")
    parser.add_argument("province_code", type=str, help="2-digit province code (e.g., '04' for Almería)")
    args = parser.parse_args()
    
    prov = args.province_code.zfill(2)
    
    # 1. Download CSV files for the specified province
    logger.info(f"Downloading data for province {prov}...")
    downloader = INEDownloader(province_code=prov)
    downloaded_paths = downloader.download_all()

    # 2. Define dynamic paths based on the province code
    DB_PATH = f"data/medea_census_{prov}.db"
    
    run_pipeline(
        db_path=DB_PATH,
        studies_path=downloaded_paths.get("studies"),
        activity_path=downloaded_paths.get("activity"),
        occupation_path=downloaded_paths.get("occupation")
    )
