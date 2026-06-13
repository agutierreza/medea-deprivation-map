import os
import ssl
import sys
import zipfile
import urllib.request
from pathlib import Path

def download_progress_hook(count, block_size, total_size):
    """Callback function to display download progress."""
    percent = int(count * block_size * 100 / total_size)
    percent = min(100, percent)  # Cap at 100%
    sys.stdout.write(f"\rDownloading shapefile: {percent}% completed ({count * block_size // (1024 * 1024)} MB of {total_size // (1024 * 1024)} MB)")
    sys.stdout.flush()

def download_and_extract_shapefiles(year: int = 2021):
    """
    Downloads and extracts the census sections shapefile for a given year.
    Uses the direct static URL format on the INE server.
    """
    base_dir = Path(__file__).resolve().parent.parent
    output_dir = base_dir / "data" / f"Seccionado_{year}"
    zip_path = base_dir / "data" / f"seccionado_{year}.zip"

    # Check if files already exist
    if output_dir.exists() and any(output_dir.iterdir()):
        print(f"Shapefiles for {year} already exist in: {output_dir}")
        return

    # Ensure data directory exists
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    url = f"https://www.ine.es/prodyser/cartografia/seccionado_{year}.zip"
    print(f"Requesting data for year {year} from: {url}")

    # Ignore SSL certification checks to prevent environment issues
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # Set up SSL context globally for urllib
    opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
    urllib.request.install_opener(opener)

    try:
        # Request with a standard User-Agent header
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )

        print("Connecting to INE server...")
        with urllib.request.urlopen(req) as response:
            total_size = int(response.info().get('Content-Length', 0))
            
        print(f"Starting download ({total_size // (1024 * 1024)} MB)...")
        # Download file using the progress hook
        urllib.request.urlretrieve(url, filename=zip_path, reporthook=download_progress_hook)
        print("\nDownload finished successfully!")

        print(f"Extracting files to: {output_dir}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
        
        # If the ZIP file extracted into a nested directory of the same name, hoist the files up
        nested_dir = output_dir / f"Seccionado_{year}"
        if nested_dir.is_dir():
            print(f"Hoisting files from nested directory: {nested_dir}...")
            for item in nested_dir.iterdir():
                item.rename(output_dir / item.name)
            nested_dir.rmdir()
            
        print("Extraction completed!")

    except Exception as e:
        print(f"\nError occurred during retrieval: {e}")
        if zip_path.exists():
            zip_path.unlink()
        sys.exit(1)
    finally:
        # Clean up the zip file to keep the workspace clean
        if zip_path.exists():
            zip_path.unlink()

if __name__ == "__main__":
    # Allow passing a year argument or default to 2021
    target_year = 2021
    if len(sys.argv) > 1:
        try:
            target_year = int(sys.argv[1])
        except ValueError:
            print("Invalid year specified. Defaulting to 2021.")
    
    download_and_extract_shapefiles(target_year)
