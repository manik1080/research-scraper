import requests
from bs4 import BeautifulSoup
from serpapi import search as GoogleSearch
import spacy
nlp = spacy.load("en_core_web_sm")


class Scraper:
    def __init__(self):
        '''
                Defining headers to simulate browser visit to avoid scraper-block.
                Headers rotate.
        '''
        self.user_agents = [
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:55.0) Gecko/20100101 Firefox/55.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
        "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
        "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
        "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
        ]
        self.header_counter = 0
        self.header_len = len(self.user_agents)

    def make_headers(self):
        '''
                Create Headers parameter and increment header_counter
        '''
        headers = {
                  'User-Agent': self.user_agents[self.header_counter]
                  }
        self.header_counter = (self.header_counter + 1) % self.header_len
        return headers
    
    def get_content(self, url: str):
        '''
                Get BeautifulSoup tree output
        '''
        response = requests.get(url)
        
        webpage_content = response.content
        soup = BeautifulSoup(webpage_content, 'html.parser')
        return soup

    def get_complete_content(self, url):
        '''
                Get text content of entire webpage.
                    (Includes links, button texts and other noisy text)
        '''
        def tag_visible(element):
            if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
                return False
            if isinstance(element, Comment):
                return False
            return True

        def get_text(body):
            soup = BeautifulSoup(body, 'html.parser')
            texts = soup.findAll(string=True)
            visible_texts = filter(tag_visible, texts)
            return u" ".join(t.strip() for t in visible_texts)

        def text_from_html(url):
            req = urllib.request.Request(url=url,
                                         headers={'User-Agent': 'Mozilla/5.0'})
            html = urllib.request.urlopen(req).read()
            return get_text(html)
        return text_from_html(url)

    def extract(self, url: str, content=['title', 'abstract', 'references', 'links'], backup_title='NOT FOUND') -> dict:
        '''
                Extracting webpage content based on the content argument
                Returns a python dictionary
        '''
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


###########################################################
####### queryScraper does not always produce output #######
###########################################################
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
