import os
import pandas as pd
import numpy as np
from src.medea import MedeaCalculator, TractRawData
from src.db import DatabaseManager

def main():
    # Ensure data dir exists
    os.makedirs("data", exist_ok=True)
    
    # 1. Test calculation with missing data (zero denominator)
    t1 = TractRawData(
        tract_id="2906701001",
        unemployed=100, economically_active=500, # 20%
        manual_workers=200, employed_population=400, # 50%
        temporary_employees=100, total_employees=300, # 33.3%
        insufficient_education_16_plus=150, total_population_16_plus=1000, # 15%
        insufficient_education_16_29=20, total_population_16_29=200 # 10%
    )
    
    t2 = TractRawData(
        tract_id="2906701002",
        unemployed=200, economically_active=400, # 50% (High deprivation)
        manual_workers=300, employed_population=400, # 75%
        temporary_employees=200, total_employees=300, # 66.6%
        insufficient_education_16_plus=400, total_population_16_plus=1000, # 40%
        insufficient_education_16_29=80, total_population_16_29=200 # 40%
    )
    
    # Tract with zero youth (will cause NaN)
    t3 = TractRawData(
        tract_id="2906701003",
        unemployed=10, economically_active=100, 
        manual_workers=20, employed_population=90, 
        temporary_employees=10, total_employees=80, 
        insufficient_education_16_plus=5, total_population_16_plus=150, 
        insufficient_education_16_29=0, total_population_16_29=0 # 0 denominator -> NaN
    )
    
    calc1 = MedeaCalculator.calculate_percentages(t1)
    calc2 = MedeaCalculator.calculate_percentages(t2)
    calc3 = MedeaCalculator.calculate_percentages(t3)
    
    print(f"Tract 3 Youth Edu Pct: {calc3['youth_education_pct']} (Should be nan)")
    
    # 2. Test PCA
    # Add a few more mock tracts so PCA works (needs more samples than features ideally)
    data = [calc1, calc2, calc3]
    for i in range(4, 10):
        data.append({
            "tract_id": f"290670100{i}",
            "unemployment_pct": 15 + i*2,
            "manual_pct": 40 + i,
            "temporary_pct": 20 + i*3,
            "education_pct": 10 + i*2,
            "youth_education_pct": 5 + i
        })
        
    df = pd.DataFrame(data)
    result_df = MedeaCalculator.calculate_pca_index(df)
    
    print("\nPCA Results:")
    print(result_df[['tract_id', 'unemployment_pct', 'medea_score']].to_string())
    
    # 3. Test Database storage
    db_path = "data/malaga_census.db"
    db = DatabaseManager(db_path)
    
    for row in result_df.to_dict('records'):
        # Handle nan for sqlite (convert to None)
        cleaned_row = {k: (None if pd.isna(v) else v) for k, v in row.items()}
        db.insert_medea_results(cleaned_row["tract_id"], cleaned_row)
        
    print("\nDB retrieval for Tract 3 (with missing data):")
    db_res = db.get_medea_results("2906701003")
    print(db_res)

if __name__ == "__main__":
    main()
