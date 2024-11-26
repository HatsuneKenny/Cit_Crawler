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

MAX_URLS = 5000  # Maximální počet URL k prozkoumání (můžeš zvýšit)
OUTPUT_FILE = "scraped_data.csv"

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

# Funkce pro stahování obrázků
def download_images(soup, base_url):
    images = soup.find_all('img')
    image_urls = []
    
    for img in images:
        img_url = img.get('src')
        if not img_url:
            continue
        if img_url.startswith('http'):
            image_urls.append(img_url)
        else:
            image_urls.append(base_url + img_url)
    
    # Create a directory to store images
    if not os.path.exists("images"):
        os.mkdir("images")
    
    for i, img_url in enumerate(image_urls):
        try:
            img_data = requests.get(img_url).content
            img_name = os.path.join("images", f"image_{i}.jpg")
            with open(img_name, 'wb') as f:
                f.write(img_data)
            print(f"Downloaded image {i+1}")
        except Exception as e:
            print(f"Failed to download image {img_url}: {e}")

# Funkce pro stahování dat z článků
def scrape_article(url):
    """Stahuje obsah článku."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Stahování obrázků
        download_images(soup, url)

        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else 'No title'
        category = soup.find('meta', {'name': 'article:section'})  # Přidání kategorie, pokud existuje
        category = category['content'] if category else 'No category'
        
        comments = soup.find('span', {'class': 'comments-count'})  # Počet komentářů
        comments = comments.get_text(strip=True) if comments else '0'
        
        images = len(soup.find_all('img'))  # Počet obrázků
        content = ' '.join([p.get_text(strip=True) for p in soup.find_all('p')])

        # Datum vytvoření
        date = soup.find('meta', {'name': 'article:published_time'})
        date = date['content'] if date else 'No date'

        return {
            "url": url, 
            "title": title, 
            "category": category, 
            "comments": comments, 
            "images": images, 
            "content": content, 
            "date": date
        }
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

# Funkce pro paralelní stahování
def scrape_multiple_urls_parallel(urls):
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(scrape_article, urls))
    return [res for res in results if res]

# Funkce pro ukládání dat do CSV
def save_to_csv(data, filename):
    if not data:
        print("No data to save!")
        return

    with open(filename, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=data[0].keys())
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

    # Kontrola velikosti souboru
    import os
    file_size = os.path.getsize(OUTPUT_FILE)
    print(f"File size: {file_size / (1024 * 1024):.2f} MB")
