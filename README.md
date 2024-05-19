# research-scraper
This script scrapes contents of research papers and returns a python dictionary. Currently supports PubMed and Nature.

Usage is shown in main.py

- > Clone repository or copy code from paper_scraper.py

- > import into your script and use the extract function of the Scraper class to extract as dictionary

---
Arguments for extract:

        - > url: url of the article/paper

        - > content: The content to be extracted, like 'abstract', 'references', 'links', 'introduction' (SHOULD BE LOWERCASE AND STRIPPED)


Future work:

        - > implement proxy rotation
    
        - > implement recursive search by scraping citation links
    
        - > support for pdf

