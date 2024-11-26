import requests
from bs4 import BeautifulSoup
import csv
import os
from concurrent.futures import ThreadPoolExecutor
import time

# Konfigurace sběru dat pro více stránek
START_URLS = [
    "https://www.novinky.cz",  # Novinky.cz
    "https://www.idnes.cz",    # iDnes.cz
    "https://www.aktualne.cz"  # Aktuálně.cz
]

MAX_URLS = 5000  # Maximální počet URL k prozkoumání
OUTPUT_FILE = "scraped_data.csv"
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB

# Funkce pro sběr URL článků
def collect_article_urls(base_url):
    """Sbírá odkazy na články z dané domény."""
    collected_urls = set()
    to_visit = [base_url]
    visited_urls = set()

    while to_visit and len(collected_urls) < MAX_URLS:
        current_url = to_visit.pop(0)
        if current_url in visited_urls:
            continue
        visited_urls.add(current_url)

        try:
            response = requests.get(current_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Vyhledávání všech odkazů na články
            for link in soup.find_all('a', href=True):
                url = link['href']
                if base_url in url and url not in collected_urls:  # Zajistíme, že to bude odkaz na stejnou doménu
                    collected_urls.add(url)
                    to_visit.append(url)
        except Exception as e:
            print(f"Error collecting URLs from {current_url}: {e}")

    return list(collected_urls)

# Funkce pro stahování dat z článků
def scrape_article(url):
    """Stahuje obsah článku."""
    try:
        response = requests.get(url)
        response.raise_for_status()

        # Kontrola, zda stránka není prázdná
        if not response.text.strip():  # Pokud je obsah prázdný, pokračujeme dál
            print(f"Skipping empty page: {url}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Titulek článku
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else 'No title'
        
        # Obsah článku
        content = ' '.join([p.get_text(strip=True) for p in soup.find_all('p')])

        # Počet obrázků
        images = len(soup.find_all('img'))
        
        # Kategorie článku
        category = soup.find('meta', {'property': 'article:section'})
        category = category['content'] if category else 'No category'

        # Počet komentářů (pokud je dostupný)
        comments = soup.find('a', {'class': 'comments-link'})
        comments_count = comments.get_text(strip=True) if comments else 'No comments'

        # Datum publikace
        date = soup.find('meta', {'property': 'article:published_time'})
        date = date['content'] if date else 'No date'

        # Další metadaty, které bychom mohli přidat
        author = soup.find('meta', {'name': 'author'})
        author = author['content'] if author else 'No author'

        # Počet sdílení na sociálních sítích
        share_count = soup.find('div', {'class': 'social-share-count'})
        share_count = share_count.get_text(strip=True) if share_count else 'No share count'

        # Kontrola, zda článek není prázdný
        if not content.strip():  # Pokud obsah článku je prázdný, ignorujeme stránku
            print(f"Skipping empty article content: {url}")
            return None

        return {
            "url": url,
            "title": title,
            "content": content,
            "images": images,
            "category": category,
            "comments_count": comments_count,
            "date": date,
            "author": author,
            "share_count": share_count
        }
    except requests.exceptions.RequestException as e:
        print(f"Error scraping {url}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error scraping {url}: {e}")
        return None

# Funkce pro paralelní stahování
def scrape_multiple_urls_parallel(urls):
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(scrape_article, urls))
    return [res for res in results if res]

# Funkce pro kontrolu velikosti souboru
def check_file_size(file_path):
    if os.path.exists(file_path):
        return os.path.getsize(file_path)
    return 0

# Funkce pro ukládání dat do CSV
def save_to_csv(data, filename):
    if not data:
        print("No data to save!")
        return

    if check_file_size(filename) > MAX_FILE_SIZE:
        print(f"File size exceeds {MAX_FILE_SIZE / 1024 / 1024 / 1024} GB. Stopping.")
        return

    file_exists = os.path.exists(filename)
    
    with open(filename, mode='a', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=data[0].keys())
        if not file_exists:
            writer.writeheader()
        writer.writerows(data)
    print(f"Data successfully saved to {filename}.")

# Hlavní program
if __name__ == "__main__":
    all_collected_urls = []

    # Sbíráme URL z více stránek
    for start_url in START_URLS:
        print(f"Collecting URLs from {start_url}...")
        urls = collect_article_urls(start_url)
        all_collected_urls.extend(urls)
        print(f"Collected {len(urls)} URLs from {start_url}")

    print(f"Total collected URLs: {len(all_collected_urls)}")

    # Sbíráme data z článků
    print("Scraping data from articles...")
    scraped_data = scrape_multiple_urls_parallel(all_collected_urls)

    # Ukládáme data do CSV
    print("Saving data to CSV...")
    save_to_csv(scraped_data, OUTPUT_FILE)
