import os
import requests
import pandas as pd
from urllib.parse import quote

# Target repository info
REPO_BASE_URL = "https://raw.githubusercontent.com/akshithsrinivas23bce5078/web-scraping-project/main/sikkim_policy_briefs/"
LOCAL_BASE_DIR = "sikkim_policy_briefs"
EXCEL_PATH = os.path.join("scraped_results", "sikkim_policy_files_index.xlsx")

# Hierarchical mapping of the 6 policy PDF files
PDF_HIERARCHY = {
    "Consolidated_Policies": [
        "Sikkim - consolidated policies.pdf",
        "Sikkim Policies.pdf"
    ],
    "Environment_and_Green": [
        "Sikkim Green Policy _ A Policy Brief _ O.P. Jindal Global University.pdf"
    ],
    "International_and_World_Bank": [
        "World Bank Document Policies.pdf"
    ],
    "Agriculture_and_Food": [
        "food and agriculture policies.pdf"
    ],
    "Sustainable_Development_and_SDG": [
        "sikkim sustainable development goals, policies and programmes for their attention.pdf"
    ]
}

def get_existing_excel_filenames():
    """Read the existing Excel file and return a set of filenames that are already indexed."""
    existing_files = set()
    if os.path.exists(EXCEL_PATH):
        try:
            df = pd.read_excel(EXCEL_PATH)
            if 'Relative Path' in df.columns:
                for path in df['Relative Path'].dropna():
                    filename = os.path.basename(str(path))
                    if filename:
                        existing_files.add(filename)
            print(f"Loaded existing index from Excel. Found {len(existing_files)} already indexed files.")
        except Exception as e:
            print(f"Warning: Could not read existing Excel index ({e}). Starting fresh.")
    else:
        print("No existing Excel index found. All target files will be checked for download.")
    return existing_files

def download_file(category, filename):
    # Construct paths
    save_dir = os.path.join(LOCAL_BASE_DIR, category)
    save_path = os.path.join(save_dir, filename)
    os.makedirs(save_dir, exist_ok=True)
    
    clean_name = filename.encode('ascii', 'replace').decode('ascii')
    
    # Try downloading from hierarchical path first, fallback to flat path if 404
    urls_to_try = [
        f"{REPO_BASE_URL}{category}/{quote(filename)}",
        f"{REPO_BASE_URL}{quote(filename)}"
    ]
    
    for url in urls_to_try:
        try:
            print(f"Trying download from: {url}")
            response = requests.get(url, stream=True, timeout=60)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                print(f"      [OK] Saved to: {category}/{filename} ({os.path.getsize(save_path)} bytes)")
                return True
            elif response.status_code != 404:
                print(f"      [FAIL] HTTP Status Code: {response.status_code}")
        except Exception as e:
            print(f"      [FAIL] Error: {e}")
            
    print(f"      [ERROR] Could not download {clean_name} from any source.")
    return False

def main():
    print("=========================================================")
    print("Downloading Latest Policy PDFs hierarchically from GitHub")
    print("=========================================================")
    print(f"Target Repo URL: {REPO_BASE_URL}")
    print(f"Saving locally to hierarchical structure under: {os.path.abspath(LOCAL_BASE_DIR)}\n")
    
    # Get the list of filenames already recorded in the Excel sheet
    existing_files = get_existing_excel_filenames()
    
    success_count = 0
    skipped_count = 0
    total_files = 0
    
    for category, files in PDF_HIERARCHY.items():
        print(f"\nCategory: {category}")
        print("-" * 50)
        for file in files:
            total_files += 1
            # Skip if the file is already listed in the Excel sheet
            if file in existing_files:
                print(f"Skipping download of: {file} (Already present in Excel index)")
                skipped_count += 1
            else:
                if download_file(category, file):
                    success_count += 1
                
    print("\n=========================================================")
    print(f"Completed! Successfully downloaded {success_count}, skipped {skipped_count} of {total_files} PDF files.")
    print("=========================================================")

if __name__ == "__main__":
    main()
