from paper_scraper import Scraper
import pandas as pd
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

def scrape_single_url(scraper, url):
    data = scraper.extract(url=url, content=['title', 'abstract', 'links'])
    return data

if __name__ == '__main__':
    scraper = Scraper()
    initial_url = "https://pubmed.ncbi.nlm.nih.gov/38186573"
    data = scraper.extract(url=initial_url, content=['title', 'abstract', 'links'])

    df = {'title': [data['title']], 'abstract': [data['abstract']]}
    links = [i for i in list(data['links'].values())]
    counter = 1

    max_workers = 5 
    scraped_urls = set()
    scraped_urls.add(initial_url)

    while links and counter < 100:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(scrape_single_url, scraper, link): link for link in links[:max_workers]}

            for future in as_completed(futures):
                link = futures[future]
                try:
                    data = future.result()
                    if data['abstract'] != 'NOT_FOUND' and link not in scraped_urls:
                        counter += 1
                        df['title'].append(data['title'])
                        df['abstract'].append(data['abstract'])
                        scraped_urls.add(link)
                        new_links = [i for i in list(data['links'].values()) if i not in scraped_urls]
                        links.extend(new_links)
                except Exception as e:
                    print(f"Error scraping {link}: {e}")
                links = links[max_workers:]

    df = pd.DataFrame(df)
    files = os.listdir(r'C:/Users/91880/Downloads/paper_scraper/extracted')
    num = len(list(filter(lambda x: x.endswith('csv'), files)))
    output_path = f"extracted/{counter}_{num}.csv"
    df.to_csv(output_path, index=False)
    print("Extracted ", counter, " files and saved at ", output_path)
