import os
import requests
from urllib.parse import quote

# Target repository info
REPO_BASE_URL = "https://raw.githubusercontent.com/akshithsrinivas23bce5078/web-scraping-project/main/sikkim_policy_briefs/"
LOCAL_DIR = "latest_pdfs"

# List of the 6 policy PDF files in the repository
PDF_FILES = [
    "Sikkim - consolidated policies.pdf",
    "Sikkim Green Policy _ A Policy Brief _ O.P. Jindal Global University.pdf",
    "Sikkim Policies.pdf",
    "World Bank Document Policies.pdf",
    "food and agriculture policies.pdf",
    "sikkim sustainable development goals, policies and programmes for their attention.pdf"
]

def download_file(url, save_path):
    # Sanitize printable name to avoid encoding errors on Windows terminal
    clean_name = os.path.basename(save_path).encode('ascii', 'replace').decode('ascii')
    print(f"Downloading: {clean_name}...")
    
    try:
        response = requests.get(url, stream=True, timeout=60)
        if response.status_code == 200:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"      [OK] Saved as: {os.path.basename(save_path)} ({os.path.getsize(save_path)} bytes)")
            return True
        else:
            print(f"      [FAIL] HTTP Status Code: {response.status_code}")
            return False
    except Exception as e:
        print(f"      [FAIL] Error: {e}")
        return False

def main():
    print("=========================================================")
    print("Downloading Latest Policy PDFs from GitHub Repository")
    print("=========================================================")
    print(f"Target URL: {REPO_BASE_URL}")
    print(f"Saving to:  {os.path.abspath(LOCAL_DIR)}\n")
    
    success_count = 0
    for file in PDF_FILES:
        # Properly URL encode filename (handles spaces and special characters)
        encoded_filename = quote(file)
        url = REPO_BASE_URL + encoded_filename
        save_path = os.path.join(LOCAL_DIR, file)
        
        if download_file(url, save_path):
            success_count += 1
        print("-" * 50)
        
    print(f"\nCompleted! Successfully downloaded {success_count} of {len(PDF_FILES)} PDF files.")

if __name__ == "__main__":
    main()
