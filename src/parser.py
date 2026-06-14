import pandas as pd
import logging
from typing import Iterator, Dict, Optional
import re
from src.medea import TractRawData

logger = logging.getLogger(__name__)

class LocalDataParser:
    """Parses local bulk data CSV files for the 2021 Census."""
    
    def __init__(self, 
                 studies_path: Optional[str] = None, 
                 activity_path: Optional[str] = None, 
                 occupation_path: Optional[str] = None):
        self.studies_path = studies_path
        self.activity_path = activity_path
        self.occupation_path = occupation_path
        
    def _read_and_clean_csv(self, path: str) -> pd.DataFrame:
        """Reads a CSV file, cleans headers and the Total column."""
        logger.info(f"Loading data from {path}")
        df = pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype={"Total": str}, low_memory=False)
        
        # Strip BOM from columns if present
        df.columns = df.columns.str.replace(r'^\ufeff', '', regex=True)
        
        # Clean and convert the Total column to integer. Lone '.' represents missing/confidential cells and is replaced with '0'.
        total_clean = df["Total"].fillna("0").str.strip().replace(".", "0", regex=False)
        df["Total_int"] = total_clean.str.replace(".", "", regex=False).astype(int)
        
        # Filter to only keep rows representing census tracts (Secciones that start with 10 digits)
        # We also need Periodo = 2021 and Sexo = "Total".
        valid_rows = (df["Periodo"] == 2021) & (df["Sexo"] == "Total") & df["Secciones"].notna()
        df = df[valid_rows].copy()
        
        # Extract the 10-digit tract ID
        df["tract_id"] = df["Secciones"].apply(
            lambda x: re.match(r"^(\d{10})", str(x)).group(1) if re.match(r"^(\d{10})", str(x)) else None
        )
        return df[df["tract_id"].notna()]

    def parse_data(self) -> Dict[str, TractRawData]:
        """
        Parses all available files and returns a dictionary of TractRawData objects
        keyed by tract_id.
        """
        tracts: Dict[str, TractRawData] = {}
        combined_data: Dict[str, Dict[str, int]] = {}

        # Parse Studies (Education)
        if self.studies_path:
            df_edu = self._read_and_clean_csv(self.studies_path)
            for tract_id, group in df_edu.groupby("tract_id"):
                total_16_plus = group[group["Nivel de formación alcanzado"] == "Total"]["Total_int"].sum()
                insufficient = group[group["Nivel de formación alcanzado"] == "Educación primaria e inferior"]["Total_int"].sum()
                
                if tract_id not in combined_data:
                    combined_data[tract_id] = {}
                combined_data[tract_id]["total_population_16_plus"] = total_16_plus
                combined_data[tract_id]["insufficient_education_16_plus"] = insufficient

        # Parse Activity (Unemployment)
        if self.activity_path:
            df_act = self._read_and_clean_csv(self.activity_path)
            for tract_id, group in df_act.groupby("tract_id"):
                unemployed = group[group["Relación con la actividad"] == "Parado/a"]["Total_int"].sum()
                employed = group[group["Relación con la actividad"] == "Ocupado/a"]["Total_int"].sum()
                
                if tract_id not in combined_data:
                    combined_data[tract_id] = {}
                combined_data[tract_id]["unemployed"] = unemployed
                combined_data[tract_id]["economically_active"] = unemployed + employed

        # Parse Occupation (Manual Workers)
        if self.occupation_path:
            df_occ = self._read_and_clean_csv(self.occupation_path)
            for tract_id, group in df_occ.groupby("tract_id"):
                total_employed = group[group["Ocupación"] == "Total"]["Total_int"].sum()
                manual_1 = group[group["Ocupación"] == "Trabajadores cualificados y oficiales/operarios de nivel bajo"]["Total_int"].sum()
                manual_2 = group[group["Ocupación"] == "Ocupaciones elementales"]["Total_int"].sum()
                
                if tract_id not in combined_data:
                    combined_data[tract_id] = {}
                combined_data[tract_id]["manual_workers"] = manual_1 + manual_2
                combined_data[tract_id]["employed_population"] = total_employed

        # Construct TractRawData objects
        for tract_id, data in combined_data.items():
            tracts[tract_id] = TractRawData(
                tract_id=tract_id,
                unemployed=data.get("unemployed", 0),
                economically_active=data.get("economically_active", 0),
                manual_workers=data.get("manual_workers", 0),
                employed_population=data.get("employed_population", 0),
                temporary_employees=0,  # Not available
                total_employees=0,      # Not available
                insufficient_education_16_plus=data.get("insufficient_education_16_plus", 0),
                total_population_16_plus=data.get("total_population_16_plus", 0),
                insufficient_education_16_29=0, # Not available
                total_population_16_29=0        # Not available
            )
            
        return tracts

    def yield_tract_data(self) -> Iterator[TractRawData]:
        """Convenience method to yield objects directly."""
        yield from self.parse_data().values()
