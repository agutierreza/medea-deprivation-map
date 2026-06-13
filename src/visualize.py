import sqlite3
import pandas as pd
import geopandas as gpd
from pathlib import Path

import argparse

def main():
    parser = argparse.ArgumentParser(description="Generate MEDEA map for a specific province.")
    parser.add_argument("province_code", type=str, help="2-digit province code (e.g., '04' for Almería)")
    args = parser.parse_args()
    
    prov = args.province_code.zfill(2)
    db_path = f"data/medea_census_{prov}.db"
    
    print(f"Loading MEDEA results from database {db_path}...")
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM medea_results WHERE medea_score IS NOT NULL", conn)
    conn.close()
    
    if df.empty:
        print(f"No results found in {db_path}. Did you run main.py first?")
        return
        
    print("Loading INE Shapefile (this might take a moment)...")
    shp_path = "data/Seccionado_2021/SECC_CE_20210101.shp"
    gdf = gpd.read_file(shp_path)
    
    print(f"Filtering shapefile for Province (Code {prov})...")
    # CUSEC is the 10-digit tract ID in the INE shapefile
    gdf_filtered = gdf[gdf["CUSEC"].str.startswith(prov)].copy()
    
    print("Joining geographic data with MEDEA scores...")
    # Merge the GeoDataFrame with our pandas DataFrame
    merged_gdf = gdf_filtered.merge(df, left_on="CUSEC", right_on="tract_id", how="inner")
    
    # We need to project to WGS84 (lat/lon) for Folium
    print("Projecting to WGS84...")
    merged_gdf = merged_gdf.to_crs(epsg=4326)
    
    # Select columns to display in the tooltip
    merged_gdf = merged_gdf[[
        "tract_id", "NCA", "NMUN", "CDIS", "medea_score", 
        "unemployment_pct", "manual_pct", "education_pct", "geometry"
    ]]
    
    print("Generating interactive HTML map...")
    # Geopandas explore() makes a beautiful Folium map automatically
    m = merged_gdf.explore(
        column="medea_score",
        cmap="YlOrRd", # Yellow to Red (Red = High Deprivation)
        scheme="quantiles", # Group by quantiles to show relative deprivation
        k=5, # 5 quintiles (Very Low, Low, Medium, High, Very High)
        tooltip=[
            "tract_id", "NMUN", "CDIS", "medea_score", 
            "unemployment_pct", "manual_pct", "education_pct"
        ],
        popup=True,
        tiles="CartoDB positron", # Clean, light basemap
        name=f"MEDEA Index (Province {prov} 2021)"
    )
    
    # Save the map
    output_html = f"data/medea_map_{prov}.html"
    m.save(output_html)
    print(f"Success! Map saved to: {Path(output_html).absolute()}")

if __name__ == "__main__":
    main()
