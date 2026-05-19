"""
==========================================================
 Sikkim Policy Web Scraper
 ---------------------------------------------------------
 This script performs web scraping for Sikkim policy
 information using the PDF documents as a knowledge base.
 
 Pipeline:
   1. Extract text from all PDFs in sikkim_policy_briefs/
   2. Use TF-IDF to identify top policy keywords
   3. Scrape government & policy websites for each keyword
   4. Parse and structure the results
   5. Export to CSV and JSON
==========================================================
"""

import os
import re
import sys
import json
import time
import glob
import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
import PyPDF2
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.corpus import stopwords

# ──────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(BASE_DIR, "sikkim_policy_briefs")
OUTPUT_DIR = os.path.join(BASE_DIR, "scraped_results")

# Scraping settings
REQUEST_TIMEOUT = 15          # seconds
DELAY_BETWEEN_REQUESTS = 2   # seconds (be polite to servers)
MAX_RESULTS_PER_SOURCE = 10  # max items to extract per website
TOP_N_KEYWORDS = 20          # number of keywords to extract from PDFs

# HTTP headers to mimic a real browser
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# STEP 1 : EXTRACT TEXT FROM PDFs
# ──────────────────────────────────────────────

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text content from a single PDF file."""
    text = ""
    try:
        reader = PyPDF2.PdfReader(pdf_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        logger.info(f"  Extracted {len(reader.pages)} pages from {os.path.basename(pdf_path)}")
    except Exception as e:
        logger.warning(f"  Could not read {os.path.basename(pdf_path)}: {e}")
    return text


def extract_all_pdfs(pdf_dir: str) -> dict:
    """
    Extract text from all PDFs in the given directory.
    Returns a dict: {filename: extracted_text}
    """
    logger.info("=" * 60)
    logger.info("STEP 1: Extracting text from PDF documents")
    logger.info("=" * 60)

    pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))
    if not pdf_files:
        logger.error(f"No PDF files found in {pdf_dir}")
        sys.exit(1)

    pdf_texts = {}
    for pdf_path in sorted(pdf_files):
        filename = os.path.basename(pdf_path)
        logger.info(f"  Reading: {filename}")
        text = extract_text_from_pdf(pdf_path)
        if text.strip():
            pdf_texts[filename] = text

    logger.info(f"  Successfully extracted text from {len(pdf_texts)}/{len(pdf_files)} PDFs\n")
    return pdf_texts


# ──────────────────────────────────────────────
# STEP 2 : EXTRACT KEYWORDS USING TF-IDF
# ──────────────────────────────────────────────

def download_nltk_data():
    """Download required NLTK data (stopwords)."""
    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        logger.info("  Downloading NLTK stopwords...")
        nltk.download("stopwords", quiet=True)


def clean_text(text: str) -> str:
    """Clean and preprocess text for keyword extraction."""
    # Remove special characters, numbers, and extra whitespace
    text = re.sub(r"[^a-zA-Z\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.lower().strip()


def extract_keywords(pdf_texts: dict, top_n: int = TOP_N_KEYWORDS) -> list:
    """
    Use TF-IDF to extract the most important keywords/phrases
    from the combined PDF texts.
    """
    logger.info("=" * 60)
    logger.info("STEP 2: Extracting policy keywords using TF-IDF")
    logger.info("=" * 60)

    download_nltk_data()

    # Combine and clean all texts
    documents = [clean_text(text) for text in pdf_texts.values()]

    # Custom stop words: English + domain-specific noise words
    stop_words = list(stopwords.words("english")) + [
        "page", "chapter", "table", "figure", "contents", "et", "al",
        "also", "would", "could", "may", "shall", "per", "cent",
        "one", "two", "three", "four", "five", "six", "seven",
        "eight", "nine", "ten", "hundred", "thousand", "million",
        "government", "state", "india", "department", "section",
    ]

    # TF-IDF with bigrams (two-word phrases are more meaningful)
    vectorizer = TfidfVectorizer(
        max_features=500,
        ngram_range=(1, 2),       # unigrams and bigrams
        stop_words=stop_words,
        min_df=1,
        max_df=0.95,
    )

    tfidf_matrix = vectorizer.fit_transform(documents)
    feature_names = vectorizer.get_feature_names_out()

    # Average TF-IDF scores across all documents
    avg_scores = tfidf_matrix.mean(axis=0).A1
    keyword_scores = list(zip(feature_names, avg_scores))
    keyword_scores.sort(key=lambda x: x[1], reverse=True)

    # Filter: prefer multi-word and Sikkim-specific terms
    sikkim_terms = [
        "sikkim organic farming", "sikkim ecotourism", "sikkim climate change",
        "sikkim biodiversity", "sikkim green mission", "sikkim sdg",
        "sikkim sustainable development", "sikkim plastic ban",
        "sikkim hydropower", "sikkim forest policy",
        "sikkim agriculture policy", "sikkim disaster management",
        "sikkim water resources", "sikkim renewable energy",
    ]

    # Combine TF-IDF keywords with curated Sikkim-specific terms
    tfidf_keywords = [kw for kw, score in keyword_scores[:top_n]]
    all_keywords = list(dict.fromkeys(sikkim_terms + tfidf_keywords))  # deduplicate, preserve order

    logger.info(f"  Top {len(all_keywords)} keywords extracted:")
    for i, kw in enumerate(all_keywords, 1):
        logger.info(f"    {i:2d}. {kw}")

    print()
    return all_keywords


# ──────────────────────────────────────────────
# STEP 3 : SCRAPE WEBSITES FOR EACH KEYWORD
# ──────────────────────────────────────────────

def fetch_page(url: str) -> BeautifulSoup | None:
    """Fetch a web page and return a BeautifulSoup object."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")
    except requests.RequestException as e:
        logger.warning(f"  Failed to fetch {url}: {e}")
        return None


def scrape_sikkim_gov(keyword: str) -> list:
    """
    Scrape the Sikkim Government website for policy-related content.
    Uses the site's search or known policy page structures.
    """
    results = []
    search_url = f"https://sikkim.gov.in/?s={keyword.replace(' ', '+')}"

    soup = fetch_page(search_url)
    if not soup:
        return results

    # Look for article entries / search results
    articles = soup.find_all(["article", "div"], class_=re.compile(r"post|entry|result|content", re.I))
    if not articles:
        # Fallback: look for any links with relevant text
        articles = soup.find_all("a", href=True)

    for item in articles[:MAX_RESULTS_PER_SOURCE]:
        title = ""
        link = ""
        snippet = ""

        if item.name == "a":
            title = item.get_text(strip=True)
            link = item.get("href", "")
        else:
            title_tag = item.find(["h2", "h3", "h4", "a"])
            if title_tag:
                title = title_tag.get_text(strip=True)
                link_tag = title_tag.find("a") if title_tag.name != "a" else title_tag
                if link_tag:
                    link = link_tag.get("href", "")

            snippet_tag = item.find(["p", "div"], class_=re.compile(r"excerpt|summary|desc", re.I))
            if snippet_tag:
                snippet = snippet_tag.get_text(strip=True)[:300]

        if title and len(title) > 10:
            results.append({
                "source": "Sikkim Government",
                "keyword": keyword,
                "title": title[:200],
                "url": link,
                "snippet": snippet,
                "scraped_at": datetime.now().isoformat(),
            })

    return results


def scrape_india_environment_portal(keyword: str) -> list:
    """
    Scrape the India Environment Portal for Sikkim-related
    environmental policy articles.
    """
    results = []
    search_url = (
        f"http://www.indiaenvironmentportal.org.in/search/node/"
        f"sikkim%20{keyword.replace(' ', '%20')}"
    )

    soup = fetch_page(search_url)
    if not soup:
        return results

    # Search result items
    items = soup.find_all("li", class_="search-result")
    if not items:
        items = soup.find_all("div", class_=re.compile(r"search|result|node", re.I))

    for item in items[:MAX_RESULTS_PER_SOURCE]:
        title_tag = item.find(["h3", "h2", "a"])
        if not title_tag:
            continue

        title = title_tag.get_text(strip=True)
        link = ""
        if title_tag.name == "a":
            link = title_tag.get("href", "")
        else:
            a_tag = title_tag.find("a")
            if a_tag:
                link = a_tag.get("href", "")

        snippet_tag = item.find("p")
        snippet = snippet_tag.get_text(strip=True)[:300] if snippet_tag else ""

        if title and len(title) > 5:
            if link and not link.startswith("http"):
                link = "http://www.indiaenvironmentportal.org.in" + link

            results.append({
                "source": "India Environment Portal",
                "keyword": keyword,
                "title": title[:200],
                "url": link,
                "snippet": snippet,
                "scraped_at": datetime.now().isoformat(),
            })

    return results


def scrape_google_scholar(keyword: str) -> list:
    """
    Scrape Google Scholar for academic papers about Sikkim policies.
    Note: Google Scholar may block automated requests — this is best-effort.
    """
    results = []
    query = f"sikkim {keyword} policy"
    search_url = f"https://scholar.google.com/scholar?q={query.replace(' ', '+')}&hl=en"

    soup = fetch_page(search_url)
    if not soup:
        return results

    # Scholar result divs
    items = soup.find_all("div", class_="gs_ri")

    for item in items[:MAX_RESULTS_PER_SOURCE]:
        title_tag = item.find("h3", class_="gs_rt")
        if not title_tag:
            continue

        # Extract title text (remove [PDF] / [HTML] labels)
        title = title_tag.get_text(strip=True)
        title = re.sub(r"^\[.*?\]\s*", "", title)

        link = ""
        a_tag = title_tag.find("a")
        if a_tag:
            link = a_tag.get("href", "")

        snippet_tag = item.find("div", class_="gs_rs")
        snippet = snippet_tag.get_text(strip=True)[:300] if snippet_tag else ""

        # Publication info
        pub_tag = item.find("div", class_="gs_a")
        pub_info = pub_tag.get_text(strip=True) if pub_tag else ""

        if title:
            results.append({
                "source": "Google Scholar",
                "keyword": keyword,
                "title": title[:200],
                "url": link,
                "snippet": snippet,
                "publication_info": pub_info,
                "scraped_at": datetime.now().isoformat(),
            })

    return results


def scrape_niti_aayog_sdg(keyword: str) -> list:
    """
    Scrape the NITI Aayog SDG India Index for Sikkim-related SDG data.
    """
    results = []
    search_url = f"https://sdgindiaindex.niti.gov.in/#!/ranking"

    soup = fetch_page(search_url)
    if not soup:
        return results

    # This is a JS-heavy site, so we extract what's available in static HTML
    items = soup.find_all(["div", "tr", "li"], string=re.compile(r"sikkim", re.I))

    for item in items[:MAX_RESULTS_PER_SOURCE]:
        text = item.get_text(strip=True)
        if text and len(text) > 5:
            results.append({
                "source": "NITI Aayog SDG Index",
                "keyword": keyword,
                "title": text[:200],
                "url": search_url,
                "snippet": text[:300],
                "scraped_at": datetime.now().isoformat(),
            })

    return results


def scrape_all_sources(keywords: list) -> list:
    """
    Scrape all configured sources for each keyword.
    Returns a list of result dictionaries.
    """
    logger.info("=" * 60)
    logger.info("STEP 3: Scraping websites for policy data")
    logger.info("=" * 60)

    all_results = []

    # Define the scraper functions and their names
    scrapers = [
        ("Sikkim Government", scrape_sikkim_gov),
        ("India Environment Portal", scrape_india_environment_portal),
        ("Google Scholar", scrape_google_scholar),
        ("NITI Aayog SDG Index", scrape_niti_aayog_sdg),
    ]

    total_keywords = len(keywords)

    for i, keyword in enumerate(keywords, 1):
        logger.info(f"\n  [{i}/{total_keywords}] Searching for: \"{keyword}\"")

        for source_name, scraper_func in scrapers:
            logger.info(f"    → Scraping {source_name}...")
            try:
                results = scraper_func(keyword)
                all_results.extend(results)
                logger.info(f"      Found {len(results)} results")
            except Exception as e:
                logger.warning(f"      Error scraping {source_name}: {e}")

            # Polite delay between requests
            time.sleep(DELAY_BETWEEN_REQUESTS)

    logger.info(f"\n  Total results scraped: {len(all_results)}\n")
    return all_results


# ──────────────────────────────────────────────
# STEP 4 : PARSE AND STRUCTURE THE RESULTS
# ──────────────────────────────────────────────

def clean_results(results: list) -> list:
    """Clean and deduplicate scraped results."""
    logger.info("=" * 60)
    logger.info("STEP 4: Cleaning and structuring results")
    logger.info("=" * 60)

    seen_titles = set()
    cleaned = []

    for item in results:
        # Clean title
        title = item.get("title", "").strip()
        if not title or len(title) < 5:
            continue

        # Deduplicate by title
        title_lower = title.lower()
        if title_lower in seen_titles:
            continue
        seen_titles.add(title_lower)

        # Clean snippet
        item["snippet"] = item.get("snippet", "").strip()

        # Ensure URL is valid
        url = item.get("url", "")
        if url and not url.startswith("http"):
            item["url"] = ""

        cleaned.append(item)

    logger.info(f"  {len(results)} raw → {len(cleaned)} after dedup & cleaning\n")
    return cleaned


# ──────────────────────────────────────────────
# STEP 5 : SAVE RESULTS TO CSV AND JSON
# ──────────────────────────────────────────────

def save_results(results: list, keywords: list, output_dir: str):
    """Save scraped results to CSV and JSON files."""
    logger.info("=" * 60)
    logger.info("STEP 5: Saving results")
    logger.info("=" * 60)

    os.makedirs(output_dir, exist_ok=True)

    # --- Save scraped data as CSV ---
    csv_path = os.path.join(output_dir, "scraped_data.csv")
    if results:
        df = pd.DataFrame(results)
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        logger.info(f"  CSV saved: {csv_path} ({len(df)} rows)")
    else:
        logger.warning("  No results to save to CSV")

    # --- Save scraped data as JSON ---
    json_path = os.path.join(output_dir, "scraped_data.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"  JSON saved: {json_path}")

    # --- Save extracted keywords ---
    keywords_path = os.path.join(output_dir, "pdf_keywords.json")
    with open(keywords_path, "w", encoding="utf-8") as f:
        json.dump({
            "extracted_at": datetime.now().isoformat(),
            "total_keywords": len(keywords),
            "keywords": keywords,
        }, f, indent=2, ensure_ascii=False)
    logger.info(f"  Keywords saved: {keywords_path}")

    # --- Print summary ---
    print("\n" + "=" * 60)
    print("  SCRAPING COMPLETE — SUMMARY")
    print("=" * 60)
    if results:
        df = pd.DataFrame(results)
        print(f"\n  Total results:  {len(results)}")
        print(f"  Unique sources: {df['source'].nunique()}")
        print(f"\n  Results by source:")
        for source, count in df["source"].value_counts().items():
            print(f"    • {source}: {count}")
        print(f"\n  Output files:")
    else:
        print("\n  No results were scraped (websites may be blocking requests)")
        print(f"\n  Output files (may be empty):")

    print(f"    • {csv_path}")
    print(f"    • {json_path}")
    print(f"    • {keywords_path}")
    print("=" * 60 + "\n")


# ──────────────────────────────────────────────
# MAIN — RUN THE FULL PIPELINE
# ──────────────────────────────────────────────

def main():
    """Execute the full scraping pipeline."""
    print("""
    =========================================================
    |       SIKKIM POLICY WEB SCRAPER                       |
    |       PDF-Guided Web Scraping Pipeline                |
    =========================================================
    """)

    start_time = time.time()

    # Step 1: Extract text from PDFs
    pdf_texts = extract_all_pdfs(PDF_DIR)

    # Step 2: Extract keywords using TF-IDF
    keywords = extract_keywords(pdf_texts)

    # Step 3: Scrape websites for each keyword
    raw_results = scrape_all_sources(keywords)

    # Step 4: Clean and structure the results
    cleaned_results = clean_results(raw_results)

    # Step 5: Save everything
    save_results(cleaned_results, keywords, OUTPUT_DIR)

    elapsed = time.time() - start_time
    logger.info(f"Total execution time: {elapsed:.1f} seconds")


if __name__ == "__main__":
    main()
