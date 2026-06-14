import sqlite3
import pandas as pd
import geopandas as gpd
from pathlib import Path
import argparse

def main():
    parser = argparse.ArgumentParser(description="Generate MEDEA map for one or more provinces.")
    parser.add_argument("province_codes", type=str, nargs="+", help="2-digit province code(s) (e.g., '01 20 48' or '04')")
    args = parser.parse_args()
    
    prov_codes = [p.zfill(2) for p in args.province_codes]
    
    dfs = []
    for prov in prov_codes:
        db_path = f"data/medea_census_{prov}.db"
        if not Path(db_path).exists():
            print(f"Database {db_path} not found. Skipping province {prov}...")
            continue
            
        print(f"Loading MEDEA results from database {db_path}...")
        conn = sqlite3.connect(db_path)
        try:
            df = pd.read_sql_query("SELECT * FROM medea_results WHERE medea_score IS NOT NULL", conn)
            dfs.append(df)
        except Exception as e:
            print(f"Error reading from {db_path}: {e}")
        finally:
            conn.close()
            
    if not dfs:
        print("No results found. Did you run main.py first for the specified province(s)?")
        return
        
    combined_df = pd.concat(dfs, ignore_index=True)
    
    print("Loading INE Shapefile (this might take a moment)...")
    shp_path = "data/Seccionado_2021/SECC_CE_20210101.shp"
    gdf = gpd.read_file(shp_path)
    
    print(f"Filtering shapefile for Provinces ({', '.join(prov_codes)})...")
    # CUSEC is the 10-digit tract ID in the INE shapefile. The first two digits are the province code.
    gdf_filtered = gdf[gdf["CUSEC"].str.slice(0, 2).isin(prov_codes)].copy()
    
    print("Joining geographic data with MEDEA scores...")
    # Merge the GeoDataFrame with our pandas DataFrame
    merged_gdf = gdf_filtered.merge(combined_df, left_on="CUSEC", right_on="tract_id", how="inner")
    
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
        name=f"MEDEA Index (Provinces {', '.join(prov_codes)} 2021)"
    )
    
    # Save the map
    output_name = f"medea_map_{'_'.join(prov_codes)}.html"
    output_html = f"data/{output_name}"
    m.save(output_html)
    print(f"Success! Map saved to: {Path(output_html).absolute()}")

if __name__ == "__main__":
    main()
