from paper_scraper import Scraper, ThreadedExtractor


if __name__ == '__main__':
    scraper = Scraper()
    data = scraper.extract(url="", # Enter URL to be scraped
                            content=['title', 'abstract', 'references', 'links'], # This is the default content: 
                            )
    print(data.keys())

    ## ADD CODE HERE
    # Eg: print(data['abstract']) ... 


    # To extract multiple related papers, the approach used here is through
    # going through citations of the initial_url, extracting their data and
    # going through citations of each of those papers as well
    # This is computationally expensive, hence I used multi-threading to increase speed
    t_extr = ThreadedExtractor(max_workers=5, # Maximum number of concurrent threads
                               initial_url="", # Starting URL
                               content=[] # Same as above
                              )
    data = t_extr.extract(
        count=10, # Number of papers to be extracted
        return_type='pandas', # May be 'csv' or 'dict' or 'pandas'
        file_path="" #In case 'csv' selected, gice absolute path (optional)
        # By default, file_path is current working directory
    )
    data = t_extr.extend_pd( # Extends a pandas dataframe with new initial_url
        data=data, # Previously created pandas dataframe object
        initial_url, # Starting URL
        count=10 # How many more to add
    ) # Returns previous dataframe concatenated with new data
