# web-scraping-project

This project demonstrates web scraping fundamentals using Python. It covers extracting data from both websites (HTML pages) and PDF documents, giving you a foundation for building data gathering pipelines with different sources.

## Features

- **Web (HTML) Scraping:** Automatically extract and parse structured or unstructured data from websites.
- **PDF Scraping:** Extract text from PDF files for analysis.
- Simple and modular Python scripts.
- Easily extendable for additional data sources or output formats.

## Technologies Used

- **Python 3**
- [requests](https://docs.python-requests.org/en/master/): For fetching web content.
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/): For HTML parsing.
- [PyPDF2](https://github.com/py-pdf/PyPDF2): For reading PDF files.

## Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/akshithsrinivas23bce5078/web-scraping-project.git
   cd web-scraping-project
   ```

2. **Install Python dependencies:**
   ```sh
   pip install requests beautifulsoup4 PyPDF2
   ```

## Usage

### 1. Web Scraping Example (`web_scrape.py`)

This example script fetches a web page and extracts all the text within paragraph (`<p>`) tags.

```python
import requests
from bs4 import BeautifulSoup

url = 'https://example.com'  # Replace with your target URL
response = requests.get(url)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    paragraphs = soup.find_all('p')
    for p in paragraphs:
        print(p.get_text())
else:
    print('Failed to retrieve the web page')
```

### 2. PDF Scraping Example (`pdf_scrape.py`)

This script extracts all text from a PDF file.

```python
import PyPDF2

file_path = 'sample.pdf'  # Replace with your PDF path
with open(file_path, 'rb') as pdf_file:
    reader = PyPDF2.PdfReader(pdf_file)
    for page in reader.pages:
        text = page.extract_text()
        print(text)
```

## Notes

- **Respect Terms of Service:** Always check the target website’s terms of service and robots.txt before scraping.
- **PDF Extraction:** Extraction quality may vary depending on how the PDF was generated.

## Contributing

Feel free to fork this project and submit pull requests.

## License

This project is open source.

---

**Tip:** Add sample HTML and PDF files for quick testing, or expand scripts for more advanced scraping needs.
