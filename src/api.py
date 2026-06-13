import requests
import json
from typing import List, Dict, Any

API_URL = "https://www.ine.es/Censo2021/api"

def discover_metadata(table: str, variables: List[str]) -> Dict[str, Any]:
    """Queries the INE API to discover the category IDs for the given variables."""
    payload = {
        "tabla": table,
        "idioma": "ES",
        "metrica": ["SPERSONAS"],
        "variables": variables
    }
    print(f"Fetching metadata for table {table} with variables {variables}...")
    response = requests.post(API_URL, json=payload, headers={"Content-Type": "application/json"})
    if response.status_code != 200:
        print(f"Failed with {response.status_code}. Response: {response.text}")
        return []
    data = response.json()
    return data.get("metadata", [])

if __name__ == "__main__":
    # We must include a valid geographic variable (like province) to avoid 404
    # Education: Age and Education in per.ppal
    meta_edu = discover_metadata("per.ppal", ["ID_RESIDENCIA_N2", "ID_GRUPO_Q_EDAD", "ID_ESREAL_GR5"])
    if meta_edu:
        for m in meta_edu:
            if m['variable'] in ["ID_GRUPO_Q_EDAD", "ID_ESREAL_GR5"]:
                print(f"\n--- VARIABLE: {m['variable']} ({m['nombre']}) ---")
                for mod in m.get("modalidades", []):
                    print(f"  {mod['id']}: {mod['nombre']}")
            
    # Employment: Activity Status, Professional Status, Occupation in per.ocu
    meta_emp = discover_metadata("per.ocu", ["ID_RESIDENCIA_N2", "ID_RELA", "ID_SITU", "ID_OCU11"])
    if meta_emp:
        for m in meta_emp:
            if m['variable'] in ["ID_RELA", "ID_SITU", "ID_OCU11"]:
                print(f"\n--- VARIABLE: {m['variable']} ({m['nombre']}) ---")
                for mod in m.get("modalidades", []):
                    print(f"  {mod['id']}: {mod['nombre']}")
    
    # Check tracts
    print("\nFetching Census Tracts for Málaga (Province 29)...")
    meta_tracts = discover_metadata("per.ppal", ["ID_RESIDENCIA_N5"])
    if meta_tracts:
        tract_meta = next((m for m in meta_tracts if m["variable"] == "ID_RESIDENCIA_N5"), None)
        if tract_meta:
            malaga_tracts = [mod for mod in tract_meta.get("modalidades", []) if mod["id"].startswith("29") and len(mod["id"]) > 2]
            print(f"Found {len(malaga_tracts)} tracts in Málaga. First 5: {[t['id'] for t in malaga_tracts[:5]]}")
