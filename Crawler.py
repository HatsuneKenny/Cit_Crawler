import requests
from bs4 import BeautifulSoup
import csv
import time

# Konfigurace sběru dat
START_URLS = {
    "novinky": "https://www.novinky.cz",
    "idnes": "https://www.idnes.cz",
    "aktualne": "https://www.aktualne.cz"
}
MAX_SIZE_MB = 2000  # Limit dat ke stažení (2 GB)
OUTPUT_FILE = "scraped_data.csv"

# Funkce pro stahování dat z článků
def scrape_article(url, website):
    """Stahuje obsah článku z různých webů."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        if website == "novinky":
            title = soup.find('h1').get_text(strip=True) if soup.find('h1') else 'No title'
            content = ' '.join([p.get_text(strip=True) for p in soup.find_all('p')])
        elif website == "idnes":
            title = soup.find('h1', class_='document-title').get_text(strip=True) if soup.find('h1', class_='document-title') else 'No title'
            content = ' '.join([p.get_text(strip=True) for p in soup.find_all('p')])
        elif website == "aktualne":
            title = soup.find('h1').get_text(strip=True) if soup.find('h1') else 'No title'
            content = ' '.join([p.get_text(strip=True) for p in soup.find_all('p')])
        else:
            return None  # Web není podporován

        return {"url": url, "title": title, "content": content}
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

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
    scraped_data = []
    visited_urls = set()
    start_time = time.time()

    print("Starting data collection...")
    for website, start_url in START_URLS.items():
        print(f"Collecting data from {website}...")

        # Například přidáme manuální seznam URL pro každý web
        urls = [
            f"{start_url}/clanek/zpravy-novinka-1",
            f"{start_url}/clanek/zpravy-novinka-2"
        ]  # Tento seznam uprav dle skutečných URL

        for url in urls:
            if len(scraped_data) * 0.001 >= MAX_SIZE_MB:
                print("Reached maximum data size!")
                break
            if url in visited_urls:
                continue

            article_data = scrape_article(url, website)
            if article_data:
                scraped_data.append(article_data)
                visited_urls.add(url)

            # Kontrola času (např. max 6 hodin)
            elapsed_time = time.time() - start_time
            if elapsed_time > 6 * 3600:
                print("Reached maximum time limit!")
                break

    save_to_csv(scraped_data, OUTPUT_FILE)
    print("Data collection finished.")
