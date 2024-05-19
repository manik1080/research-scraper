from paper_scraper import Scraper


if __name__ == '__main__':
    scraper = Scraper()
    data = scraper.extract(url="", # Enter URL to be scraped
                            content=['title', 'abstract', 'references', 'links'], # This is the default content: 
                            )
    print(data.keys())

    ## ADD CODE HERE
    # Eg: print(data['abstract']) ... 
