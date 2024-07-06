import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import numpy as np
import urllib
import copy
import bs4
import re
import pandas as pd
import os


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

    def extract(self, url: str, content=['title', 'abstract', 'results', 'links'], backup_title='NOT_FOUND') -> dict:
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
                                    if i.get('href').startswith('http'):
                                        links[i.text.strip()] = i.get('href')
                data['links'] = links

            elif key=='abstract':
                abstract = 'NOT_FOUND'
                if 'pubmed' in url:
                    abstract = re.sub(r'\s+', ' ', ' '.join([i.text for i in soup.find(id='eng-abstract').find_all('p')]))
                else:
                    for heading in headings:
                        head = heading.text.lower().strip()
                        if head==key:
                            abstract = re.sub(r'\s+', ' ', heading.findNext('p').text).strip()
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
######## Multi-scraping citations to csv/dataframe ########
###########################################################
    
class ThreadedExtractor:
    def __init__(self, max_workers, initial_url, content=['title', 'abstract', 'links']):
        """Create ThreadedExtractor Object.

        :param max_workers: number of concurrent threads
        :type max_workers: int
        :param initial_url: the first url to be scraped
        :type initial_url: str
        :param content: content to be scraped from url
        :type content: list
        :returns: ThreadedExtractor Object
        :rtype: ThreadedExtractor
        """
        self.max_workers = max_workers
        self.initial_url = initial_url
        self.display_content = content
        self.content = content if 'links' in content else content+['links']
        self.scraper = Scraper()
        self.scrape_single_url = lambda url: self.scraper.extract(url, self.content)
        self.data = self.scrape_single_url(initial_url)
        if not self.data['links']:
            raise ValueError("No results. Try different initial url.")
        self.df = {i: [self.data[i]] for i in self.display_content}

    def extract(self, count, return_type='pandas', file_path=os.getcwd()):
        """Extract files from citations.

        :param count: number of urls to be scraped
        :type count: int
        :param return_type: function returns 'dict', 'pandas' or 'csv'
        :type return_type: str
        :param file_path: (if return_type is 'csv')Absolute path 
        :type file_path: str
        :returns: return_type specified
        """
        links = [i for i in list(self.data['links'].values())]
        counter = 1
        scraped_urls = set()
        scraped_urls.add(self.initial_url)

        while links and counter < count:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self.scrape_single_url, link):\
                           link for link in links[:self.max_workers]}

                results = []
                for future in as_completed(futures):
                    link = futures[future]
                    try:
                        data = future.result()
                        results.append((link, data))
                    except Exception as e:
                        print(f"Error scraping {link}: {e}")

            # Process all results after all threads have completed
            for link, data in results:
                if link not in scraped_urls:
                    temp_df = copy.deepcopy(self.df)
                    flag = False
                    for column in self.display_content:
                        if data[column]=='NOT_FOUND':
                            flag = True
                            break
                        else:
                            temp_df[column].append(data[column])
                    
                    if flag==True:
                        scraped_urls.add(link)
                    if flag==False:
                        counter += 1
                        self.df = copy.deepcopy(temp_df)
                        scraped_urls.add(link)
                        new_links = [i for i in list(data['links'].values()) if i not in scraped_urls]
                        links.extend(new_links)

            links = links[self.max_workers:]
        if return_type=='dict':
            return self.df
        elif return_type=='pandas':
            return pd.DataFrame(self.df)
        elif return_type=='csv':
            df = pd.DataFrame(self.df)
            if file_path.endswith('csv'):
                directory, name = os.path.split(file_path)
            else:
                directory, name = file_path, f"{self.initial_url.rstrip('/').split('/')[-1]}_{count}.csv"
            output_path = os.path.join(directory, name)
            df.to_csv(output_path, index=False)
            print("Extracted ", counter, " files and saved at ", output_path)
            return None
        else:
            raise ValueError("Incorrect return type\nMust be 'dict', 'pandas' or 'csv'")

    def extend_pd(self, data, initial_url, count):
        """Extend pandas dataframe.

        :param data: pandas DataFrame object
        :type data: pandas.DataFrame
        :param initial_url: url to start scraping from
        :type initial_url: str
        :param count: number of rows to be added
        :type count: int
        :returns: pandas.DataFrame object
        """
        self.display_content = list(data.keys())
        self.data = self.scrape(initial_url, self.content)
        if not self.data['links']:
            raise ValueError("No results. Try different initial url.")

        self.df = {i: [data[i]] for i in self.display_content if i in self.content}
        new = self.extract(count, return_type='pandas')
        concatenated = pd.concat([data, new], columns=self.display_content)

        return concatenated

###########################################################
####### queryScraper does not always produce output #######
###########################################################
class queryScraper:
    def __init__(self):
        self.scraper = Scraper()

    def get_links(self, query):
        search_url = f"https://www.google.com/search?q={'+'.join(query.split())}+research"
        response = requests.get(search_url, headers=self.scraper.get_header())
        soup = BeautifulSoup(response.content, "html.parser")

        results = []
        for link in soup.find_all('a'):
            href = link.get('href')
            if href:
                if 'url?q=' in href and 'webcache' not in href and len(link.text)>15:
                    url = href.split('url?q=')[1].split('&sa=U')[0]
                    results.append((link.text.rstrip(' › ...'), url))
        #results = [i for i in results if i is not None]
        return results[0]

    def extract(self, query: str, content=['title', 'abstract', 'references', 'links'], recur=False) -> dict:
        title, url = self.get_links(query)
        try:
            data = self.scraper.extract(url, content, backup_title=title)
        except:
            print("Error on scraping url: ", url)
        return data



if __name__ == '__main__':
    #t = ThreadedExtractor(6, "https://pubmed.ncbi.nlm.nih.gov/38186573", content=['title', 'abstract', 'links'])
    #t.extract(50, 'csv')
    s = Scraper()
    d = s.extract("https://pubmed.ncbi.nlm.nih.gov/38186573")
    #s = queryScraper()
    #d = s.extract('Asia women breast cancer under 40 pubmed')
    #print(d.keys())
    #for i in d['links']:
     #   print(d['links'][i])
    for i in d:
        print(d[i], end='\n\n')
     
