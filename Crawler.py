import requests
from bs4 import BeautifulSoup
import csv
import boto3
from urllib.parse import urljoin
from multiprocessing.dummy import Pool as ThreadPool

# Scraper pro novinky.cz
def scrape_novinky(url, visited):
    try:
        if url in visited:
            return None  # Pokud už byla stránka zpracována, přeskočíme ji
        visited.add(url)
        
        # Stáhnutí obsahu stránky
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extrahování dat
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "N/A"
        category = soup.find('div', class_='category').get_text(strip=True) if soup.find('div', class_='category') else "N/A"
        comments = soup.find('span', class_='comments-count').get_text(strip=True) if soup.find('span', class_='comments-count') else "0"
        photos_count = len(soup.find_all('img'))
        content = ' '.join([p.get_text(strip=True) for p in soup.find_all('p')])

        # Seznam odkazů na další články
        links = [urljoin(url, a['href']) for a in soup.find_all('a', href=True) if 'novinky.cz' in a['href']]

        # Filtrace článkových odkazů (můžeme přidat další podmínky pro filtrování nečlánkových URL)
        links = [link for link in links if link.startswith('https://www.novinky.cz/clanek')]

        return {
            "title": title,
            "category": category,
            "comments": comments,
            "photos_count": photos_count,
            "content": content,
            "links": links  # Vráti všechny nové odkazy k dalšímu zpracování
        }
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


# Funkce pro procházení URL
def scrape_multiple_urls(url_list):
    visited = set()  # Set pro uchovávání navštívených URL
    scraped_data = []
    pool = ThreadPool(8)  # Paralelní scraping s 8 vlákny
    while url_list:
        # Vezmeme první URL v seznamu, zpracujeme ji a přidáme její odkazy do fronty
        url = url_list.pop(0)
        result = scrape_novinky(url, visited)
        if result:
            scraped_data.append(result)
            url_list.extend(result["links"])  # Přidáme nové odkazy do fronty
    pool.close()
    pool.join()
    return scraped_data


# Uložení do CSV
def save_to_csv(data, filename="output.csv"):
    if not data:
        print("No data to save!")
        return
    keys = data[0].keys()
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
    print(f"Data successfully saved to {filename}.")


# Nahrání na S3
def upload_to_s3(file_name, bucket_name):
    s3 = boto3.client('s3')
    try:
        s3.upload_file(file_name, bucket_name, file_name)
        print(f"File {file_name} successfully uploaded to bucket {bucket_name}.")
    except Exception as e:
        print(f"Error uploading to S3: {e}")


# Hlavní funkce
if __name__ == "__main__":
    # Počáteční URL pro crawler
    urls = [
        "https://www.novinky.cz"  # Můžete začít i hlavní stránkou
    ]

    # Scraping
    scraped_data = scrape_multiple_urls(urls)

    # Uložení do CSV
    save_to_csv(scraped_data, "scraped_data.csv")

    # Nahrání na S3 (nastavte svůj bucket)
    bucket_name = "moje-s3-bucket"  # Zde nahraďte názvem svého bucketu
    upload_to_s3("scraped_data.csv", bucket_name)
