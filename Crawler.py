import requests
from bs4 import BeautifulSoup
import csv
import boto3
from multiprocessing.dummy import Pool as ThreadPool

# Scraper pro novinky.cz
def scrape_novinky(url, visited):
    if url in visited:
        return None
    visited.add(url)
    
    try:
        response = requests.get(url, timeout=10)  # Timeout přidán
        response.raise_for_status()  # Zkontroluje HTTP chyby
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extrahování dat
        title = soup.find('h1').get_text(strip=True) if soup.find('h1') else "N/A"
        category = soup.find('div', class_='category').get_text(strip=True) if soup.find('div', class_='category') else "N/A"
        comments = soup.find('span', class_='comments-count').get_text(strip=True) if soup.find('span', class_='comments-count') else "0"
        photos_count = len(soup.find_all('img'))
        content = ' '.join([p.get_text(strip=True) for p in soup.find_all('p')])

        return {
            "title": title,
            "category": category,
            "comments": comments,
            "photos_count": photos_count,
            "content": content
        }
    except requests.exceptions.Timeout:
        print(f"Timeout při pokusu o připojení k {url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Chyba při připojování k {url}: {e}")
        return None


# Funkce pro více URL
def scrape_multiple_urls(url_list):
    visited = set()  # Sada pro záznam již navštívených URL
    pool = ThreadPool(16)  # Zvýšení počtu vláken na 16 pro rychlejší zpracování
    results = pool.map(lambda url: scrape_novinky(url, visited), url_list)
    pool.close()
    pool.join()
    return [result for result in results if result is not None]


# Uložení do CSV
def save_to_csv(data, filename="scraped_data.csv"):
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
    # Ukázkový seznam URL
    urls = [
        "https://www.novinky.cz/clanek/zahranicni-evropa-ukazkovy-clanek-1",
        "https://www.novinky.cz/clanek/domaci-ukazkovy-clanek-2",
        "https://www.novinky.cz/clanek/ekonomika-ukazkovy-clanek-3"
    ]

    # Scraping
    scraped_data = scrape_multiple_urls(urls)

    # Uložení do CSV
    save_to_csv(scraped_data, "scraped_data.csv")

    # Nahrání na S3 (nastavte svůj bucket)
    bucket_name = "moje-s3-bucket"  # Nahraďte názvem svého S3 bucketu
    upload_to_s3("scraped_data.csv", bucket_name)
