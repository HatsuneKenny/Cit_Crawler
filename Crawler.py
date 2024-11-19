import requests
from bs4 import BeautifulSoup
import csv

def scrape_novinky(url, visited):
    if url in visited:
        return None

    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extrahujeme data
        title = soup.find('h1').text.strip() if soup.find('h1') else 'No title'
        category = soup.find('meta', attrs={'name': 'category'}).get('content', 'No category') if soup.find('meta', attrs={'name': 'category'}) else 'No category'
        comments = soup.find('span', class_='comments-count').text.strip() if soup.find('span', class_='comments-count') else '0'
        photos = len(soup.find_all('img'))
        content = soup.find('div', class_='article-content').text.strip() if soup.find('div', class_='article-content') else 'No content'

        visited.add(url)
        return {'title': title, 'category': category, 'comments': comments, 'photos': photos, 'content': content}

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None

def scrape_multiple_urls(urls):
    scraped_data = []
    visited = set()

    for url in urls:
        result = scrape_novinky(url, visited)
        if result:
            scraped_data.append(result)
    
    return scraped_data

def save_to_csv(data, filename='scraped_data.csv'):
    if not data:
        print("No data to save!")
        return

    keys = data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
    print(f"Data successfully saved to {filename}.")

# Vstupní URL článků
urls = [
    'https://www.novinky.cz/clanek/krimi-mohutny-vybuch-otrasl-nad-ranem-centrem-karlovych-varu-40497851',
    'https://www.novinky.cz/clanek/domaci-politici-se-prisli-rozloucit-s-marii-benesovou-40497922',
    'https://www.novinky.cz/clanek/zahranicni-lavrov-ukrajina-chce-nasazenim-atacms-eskalovat-konflikt-40497931'
]

# Scraping dat
scraped_data = scrape_multiple_urls(urls)

# Uložení dat do CSV
save_to_csv(scraped_data)
