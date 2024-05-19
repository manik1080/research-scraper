import requests
from bs4 import BeautifulSoup
from serpapi import search as GoogleSearch
from get_valid import check_proxies


class Scraper:
    def __init__(self):
        self.proxies = None
        
    
    def get_proxy_list(self):
        check_proxies()
        with open('valid-proxies.txt', 'r') as f:
            self.proxies = f.read().split('\n')
        return proxies
    
    def get_content(self, url: str):
        self.proxies = self.get_proxy_list()
        try:
            response = requests.get(url, proxies={"http": proxies[counter],
                                              "https": proxies[counter]})
        except:
            print(response.status_code, " Failed")
        finally:
            counter = counter%len(proxies) + 1
        response = requests.get(url)
        
        webpage_content = response.content
        soup = BeautifulSoup(webpage_content, 'html.parser')
        return soup
    

    def extract(self, url: str, content=['title', 'abstract', 'references', 'links'], backup_title='NOT FOUND') -> dict:
        similar = {'results': ['results', 'result', 'conclusion', 'conclusions'],
                   'references': ['references', 'citation', 'citations', 'reference', 'similar articles'],
                   }
        soup = self.get_content(url)
        head_list = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        headings = soup.find_all(head_list)
        data = {}
        links = {}

        title_found = False
        for key in content:
            if key=='title':
                try:
                    data['title'] = soup.find('h1').text.strip()
                except:
                    data['title'] = backup_title

            elif key=='links':
                for heading in headings:
                    head = heading.text.lower().strip()
                    if head in similar['references']:
                        for sibling in heading.find_next_siblings():
                            for i in sibling.findChildren(href=True):
                                if 'pubmed' in url:
                                    links[i.text.strip()] = "https://pubmed.ncbi.nlm.nih.gov" + i.get('href')
                                else:
                                    links[i.text.strip()] = i.get('href')
                data['links'] = links

            elif key=='abstract':
                abstract = 'NOT FOUND'
                for heading in headings:
                    head = heading.text.lower().strip()
                    if head==key:
                        abstract = heading.findNext('p').text.strip()
                        break
                data['abstract'] = abstract

            elif key=='results':
                results = 'NOT FOUND'
                for heading in headings:
                    head = heading.text.lower().strip()
                    if head in similar[key]:
                        results = heading.findNext('p').text.strip()
                        break
                data['results'] = results
            else:
                other = 'NOT FOUND'
                for heading in headings:
                    head = heading.text.lower().strip()
                    if head==key:
                        other = heading.findNext('p').text.strip()
                        break
                data[key.lower().strip()] = other
        return data


class queryScraper:
    def __init__(self, api_key):
        self.scraper = Scraper()
        self.api_key = api_key

    def get_url(self, query):
        params = {
            "engine": "google",
            "q": f"{query} research paper",
            "api_key": self.api_key
        }
        search = GoogleSearch(params)
        result = (search.as_dict()['organic_results'][0]['title'], search.as_dict()['organic_results'][0]['link'])
        return result

    def extract(self, query: str, content=['title', 'abstract', 'references', 'links'], recur=False) -> dict:
        title, url = self.get_url(query)
        try:
            data = self.scraper.extract(url, content, backup_title=title)
        except:
            print("Error on scraping url: ", url)
        return data
