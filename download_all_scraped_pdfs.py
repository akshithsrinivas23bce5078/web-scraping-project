import os
import json
import re
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "scraped_results", "scraped_data.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "scraped_policy_pdfs")

def sanitize_filename(filename):
    # Remove invalid characters for Windows filenames
    return re.sub(r'[\\/*?:"<>|]', "", filename).strip()

def download_pdf(url, title, idx):
    # Sanitize title for filename
    clean_title = sanitize_filename(title)
    clean_title = re.sub(r"^\[PDF\]\s*", "", clean_title)
    if len(clean_title) > 80:
        clean_title = clean_title[:80]
        
    if not clean_title.lower().endswith(".pdf"):
        clean_title += ".pdf"
        
    filename = f"{idx:03d}_{clean_title}"
    save_path = os.path.join(OUTPUT_DIR, filename)
    
    # Safe console printing name
    print_name = clean_title.encode('ascii', 'replace').decode('ascii')
    
    try:
        # User agent to bypass generic blocks
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        # Stream the request and set a 15s timeout
        response = requests.get(url, headers=headers, stream=True, timeout=15)
        
        if response.status_code == 200:
            # Check content length if available (skip files > 25MB to stay within git limits)
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > 25 * 1024 * 1024:
                print(f"[SKIP] {print_name} (File too large: {int(content_length)/(1024*1024):.2f} MB)")
                return False, url, "File too large"
                
            # Download file in chunks
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Double check size of saved file
            saved_size = os.path.getsize(save_path)
            if saved_size > 25 * 1024 * 1024:
                os.remove(save_path)
                print(f"[SKIP] {print_name} (Saved file too large: {saved_size/(1024*1024):.2f} MB)")
                return False, url, "File too large"
                
            print(f"[OK] Downloaded: {print_name} ({saved_size/1024:.1f} KB)")
            return True, url, None
        else:
            return False, url, f"HTTP {response.status_code}"
    except Exception as e:
        return False, url, str(e)

def main():
    print("=========================================================")
    print("Concurrently Downloading All Scraped PDFs from Results")
    print("=========================================================")

    if not os.path.exists(JSON_PATH):
        print(f"Error: Scraped data file not found at {JSON_PATH}")
        return

    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Filter and deduplicate PDF links
    unique_pdfs = {}
    for item in data:
        url = item.get("url") or ""
        title = item.get("title") or "Document"
        
        is_pdf = "pdf" in url.lower() or "pdf" in title.lower()
        if is_pdf and url.startswith("http"):
            # Use URL as key to deduplicate
            unique_pdfs[url] = title

    print(f"Found {len(unique_pdfs)} unique PDF links to download.")
    
    if not unique_pdfs:
        print("No PDF files found to download.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Saving files in: {OUTPUT_DIR}\n")

    # Run downloads concurrently with 12 workers
    results = []
    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {
            executor.submit(download_pdf, url, title, idx): url 
            for idx, (url, title) in enumerate(unique_pdfs.items(), 1)
        }
        
        for future in as_completed(futures):
            results.append(future.result())

    # Summary
    success_count = sum(1 for r in results if r[0])
    failed_results = [r for r in results if not r[0]]

    print("\n=========================================================")
    print("Download Summary")
    print("=========================================================")
    print(f"Successfully downloaded: {success_count} / {len(unique_pdfs)}")
    print(f"Failed downloads:        {len(failed_results)}")
    
    if failed_results:
        print("\nFirst 10 failures:")
        for idx, (_, url, err) in enumerate(failed_results[:10], 1):
            print(f"{idx}. URL: {url}\n   Reason: {err}")

if __name__ == "__main__":
    main()
