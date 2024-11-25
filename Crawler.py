import requests
from bs4 import BeautifulSoup
import csv
from concurrent.futures import ThreadPoolExecutor

# Funkce pro sběr URL
def collect_urls(start_url, max_urls=1000):
    """Sbírá odkazy na články z výchozí stránky."""
    collected_urls = set()
    visited_urls = set()
    to_visit = [start_url]

    while to_visit and len(collected_urls) < max_urls:
        current_url = to_visit.pop(0)
        if current_url in visited_urls:
            continue

        try:
            response = requests.get(current_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            for link in soup.find_all('a', href=True):
                url = link['href']
                if 'novinky.cz/clanek/' in url and url not in collected_urls:
                    collected_urls.add(url)
                    to_visit.append(url)
            visited_urls.add(current_url)
        except Exception as e:
            print(f"Error collecting URLs from {current_url}: {e}")

    return list(collected_urls)

# Funkce pro stahování dat z článků
def scrape_novinky(url, visited):
    """Stahuje obsah článku a přidává jej do seznamu navštívených."""
    if url in visited:
        return None
    visited.add(url)

    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else 'No title'
        category = soup.find('a', class_='category').get_text(strip=True) if soup.find('a', class_='category') else 'Unknown'
        comments = len(soup.find_all('div', class_='comment'))  # Pokud jsou komentáře viditelné
        images = len(soup.find_all('img'))
        content = ' '.join([p.get_text(strip=True) for p in soup.find_all('p')])
        publication_date = soup.find('time')['datetime'] if soup.find('time') else 'Unknown'

        return {
            'url': url,
            'title': title,
            'category': category,
            'comments': comments,
            'images': images,
            'content': content,
            'publication_date': publication_date
        }
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

# Paralelní stahování
def scrape_multiple_urls_parallel(urls):
    visited = set()
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda url: scrape_novinky(url, visited), urls))
    return [res for res in results if res]

# Funkce pro ukládání dat do CSV
def save_to_csv(data, filename='scraped_data.csv'):
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
    # Výchozí URL a maximální počet článků
    start_url = 'https://www.novinky.cz/'
    max_urls = 1000

    print("Collecting URLs...")
    urls = collect_urls(start_url, max_urls)
    print(f"Collected {len(urls)} URLs.")

    print("Scraping data from articles...")
    scraped_data = scrape_multiple_urls_parallel(urls)

    print("Saving data to CSV...")
    save_to_csv(scraped_data)
