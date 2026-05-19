import os
import requests
from urllib.parse import quote

# Target repository info
REPO_BASE_URL = "https://raw.githubusercontent.com/akshithsrinivas23bce5078/web-scraping-project/main/sikkim_policy_briefs/"
LOCAL_BASE_DIR = "sikkim_policy_briefs"

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
    
    success_count = 0
    total_files = 0
    
    for category, files in PDF_HIERARCHY.items():
        print(f"\nCategory: {category}")
        print("-" * 50)
        for file in files:
            total_files += 1
            if download_file(category, file):
                success_count += 1
                
    print("\n=========================================================")
    print(f"Completed! Successfully downloaded {success_count} of {total_files} PDF files.")
    print("=========================================================")

if __name__ == "__main__":
    main()
