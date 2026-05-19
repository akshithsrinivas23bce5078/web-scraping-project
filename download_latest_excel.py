import os
import requests

def download_latest_excel():
    repo_url = "https://raw.githubusercontent.com/akshithsrinivas23bce5078/web-scraping-project/main/scraped_results/sikkim_policy_files_index.xlsx"
    filename = "latest_sikkim_policy_files_index.xlsx"
    
    print("=========================================================")
    print("Downloading Latest Excel File from GitHub Repository")
    print("=========================================================")
    print(f"Target URL: {repo_url}")
    print(f"Saving to: {filename}")
    
    try:
        response = requests.get(repo_url, stream=True, timeout=15)
        if response.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"\nSuccess! Downloaded the latest Excel file: {os.path.abspath(filename)}")
            print(f"File Size: {os.path.getsize(filename)} bytes")
        elif response.status_code == 404:
            print("\nError (404): The file was not found on GitHub yet.")
            print("Make sure you commit and push 'scraped_results/sikkim_policy_files_index.xlsx' to your 'main' branch first!")
        else:
            print(f"\nFailed to download. HTTP Status: {response.status_code}")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    download_latest_excel()
