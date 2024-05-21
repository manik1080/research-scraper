import requests
from bs4 import BeautifulSoup
from serpapi import search as GoogleSearch


class Scraper:
    def __init__(self):
        self.user_agents = []
        self.num_agents = self.make_headers()

    def make_headers(self):
        url = "https://deviceatlas.com/blog/list-of-user-agent-strings"

        response = requests.get(url)
        webpage_content = response.content
        soup = BeautifulSoup(webpage_content, 'html.parser')

        self.user_agents = [{'User-Agent': i} for i in '\n'.join([j.text.strip() for j in soup.findAll('td')]).split('\n') if len(i)>0]
        return len(self.user_agents)

    def get_header(self):
        return random.choice(self.user_agents)

    def get_content(self, url: str):
        head = self.get_header()
        response = requests.get(url, headers=head)
        webpage_content = response.content
        soup = BeautifulSoup(webpage_content, 'html.parser')
        return soup

    def get_complete_content(self, url):
        def tag_visible(element):
            if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
                return False
            if isinstance(element, bs4.element.Comment):
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

    def extract(self, url: str, content=['title', 'abstract', 'references', 'links'], backup_title='NOT_FOUND') -> dict:
        similar = {'results': ['results', 'result', 'conclusion', 'conclusions'],
                   'references': ['references', 'citation', 'citations', 'reference', 'similar articles'],
                   }
        #try:
        soup = self.get_content(url)
        #except:
         #   print(f"Exception occurred. Ignoring url {url}")
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
                                    if i.get('href').startswith('http'):
                                        continue
                                    links[i.text.strip()] = "https://pubmed.ncbi.nlm.nih.gov" + i.get('href')
                                else:
                                    links[i.text.strip()] = i.get('href')
                data['links'] = links

            elif key=='abstract':
                abstract = 'NOT_FOUND'
                for heading in headings:
                    head = heading.text.lower().strip()
                    if head==key:
                        abstract = heading.findNext('p').text.strip()
                        break
                if len(abstract)<30:
                    abstract = 'NOT_FOUND'
                data['abstract'] = abstract

            elif key=='results':
                results = 'NOT_FOUND'
                for heading in headings:
                    head = heading.text.lower().strip()
                    if head in similar[key]:
                        results = heading.findNext('p').text.strip()
                        break
                if len(results)<30:
                    abstract = 'NOT_FOUND'
                data['results'] = results

            else:
                other = 'NOT_FOUND'
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
