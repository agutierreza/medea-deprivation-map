import urllib.request
import ssl
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

REGISTRY_PATH = os.path.join("data", "ine_table_registry.json")

def inspect_table(t_id):
    url = f"https://www.ine.es/jaxiT3/files/t/es/csv_bdsc/{t_id}.csv"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        res = urllib.request.urlopen(req, context=ctx, timeout=5).read(500).decode('utf-8-sig', errors='ignore')
        lines = res.split('\r\n')
        if len(lines) > 1:
            header = lines[0].lower()
            data_line = lines[1]
            
            # Identify the province code from the first column (e.g. "04 Almería")
            prov_match = re.match(r"^(\d{2})\s+", data_line)
            if not prov_match:
                return None
            
            prov_code = prov_match.group(1)
            
            # Identify the variable from the header
            var_type = None
            if "nivel de formaci" in header and "sexo" in header:
                var_type = "studies"
            elif "relaci" in header and "actividad" in header and "sexo" in header:
                var_type = "activity"
            elif "ocupaci" in header and "sexo" in header:
                var_type = "occupation"
            elif "situaci" in header and "profesional" in header and "sexo" in header:
                var_type = "situation"
            elif "edad" in header and "sexo" in header:
                var_type = "age"
                
            if var_type:
                return (prov_code, var_type, str(t_id))
    except Exception:
        pass
    return None

def build_registry():
    print("Building INE Table Registry...")
    registry = {}
    
    # We know the tables for census 2021 sections are grouped in these specific ID ranges
    ranges_to_scan = list(range(66600, 66800)) + list(range(69100, 69300)) + list(range(69900, 70200))
    
    with ThreadPoolExecutor(max_workers=30) as executor:
        results = list(executor.map(inspect_table, ranges_to_scan))
        
    for r in results:
        if r:
            prov_code, var_type, t_id = r
            if prov_code not in registry:
                registry[prov_code] = {}
            registry[prov_code][var_type] = t_id

    # Save to JSON
    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
    with open(REGISTRY_PATH, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=4, sort_keys=True)
        
    print(f"Registry successfully built and saved to {REGISTRY_PATH}")
    print(f"Mapped {len(registry)} provinces.")

if __name__ == "__main__":
    build_registry()
