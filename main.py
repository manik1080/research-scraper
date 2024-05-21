from paper_scraper import Scraper
import pandas as pd
import os


if __name__ == '__main__':
    scraper = Scraper()
    data = scraper.extract(url="https://pubmed.ncbi.nlm.nih.gov/38186573", # URL to be scraped
                            content=['title', 'abstract', 'links'],
                            )
    df = {'title': [data['title']], 'abstract': [data['abstract']]}
    links = [i for i in list(data['links'].values())]
    counter = 1
    while links and counter<100:
        data = scraper.extract(url=links[counter], # URL to be scraped
                            content=['title', 'abstract', 'links'],
                            )
        links.extend([i for i in list(data['links'].values())])
        if data['abstract']!='NOT_FOUND':
            counter += 1
            df['title'].append(data['title'])
            df['abstract'].append(data['abstract'])

    df = pd.DataFrame(df)
    files = os.listdir(r'C:/Users/91880/Downloads/paper_scraper/extracted')
    num = len(list(filter(lambda x: x.endswith('csv'), files)))
    df.to_csv(f"extracted/{counter}_{num}.csv")
    print("Extracted ", counter, " files and saved at ", f"extracted/{counter}_{num}.csv")
