from bs4 import BeautifulSoup
import math
import urllib
import urllib2
import random
import pymongowrapper
from time import sleep
import time
import inspect
import hashlib
import argparse
from collections import Counter

class GoogleLawRequest():

    STATES = {
        'ny':'4,33',
        'ca':'4,5',
        'tx':'4,44'
    }
    USER_AGENT_STRINGS = (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A'
    )

    def __init__(self, state, search_term, db, max_results, wait_time):
        print whoami()
        self.state = state.lower()
        self.search_term = search_term
        self.db = db
        self.max_results = max_results
        self.wait_time = wait_time

        self.case_urls = []
        self.result_urls = []
        self.result_nums = []
        self.result_counter = 0

    # taken from google scholar scraper https://github.com/adeel/google-scholar-scraper/blob/master/src/gsscraper.py
    def _gen_fake_google_id(self):
        return hashlib.md5(str(random.random()).encode("utf-8")).hexdigest()[:16]

    def get_soup(self, url):
        print whoami()
        opener = urllib2.build_opener()
        gid = self._gen_fake_google_id()
        opener.addheaders = [('User-agent', random.sample(self.USER_AGENT_STRINGS, 1)), ('Cookie', 'GSP=ID=%s:CF=4' % gid )]
        response = opener.open(url)
        soup = BeautifulSoup(response)
        return soup

    def search(self):
        print whoami()
        # get response object
        BASE_URL = 'https://scholar.google.com/scholar?'
        url = BASE_URL + urllib.urlencode({'hl' : 'en', 'as_sdt' : self.STATES[self.state], 'q' : self.search_term})
        soup = self.get_soup(url)

        # get data from main page
        self.get_num_results(soup)
        self.get_results_urls(url) # but you need to keep looking
        self.get_case_urls_from_result_url(base_url = "", url = url, offset = 0)

        BASE_URL = 'https://scholar.google.com'
        while self.case_urls:
            sleep(random.randint(0, self.wait_time))
            # retrieve more result urls
            if self.result_urls:
                result_url = self.result_urls.pop(0)
                self.get_case_urls_from_result_url(BASE_URL, **result_url)
            # retrieve more individual cases
            t =  self.case_urls.pop(0)
            print t
            print type(t)
            self.get_case_text(base_url = BASE_URL, **t)

    def get_num_results(self, soup):
        print whoami()
        result = soup.find('div', {'id' : 'gs_ab_md'})
        num = int(result.text.split(" ")[1].replace(",", ""))
        self.num_results = num
        self.max_results = min(int(self.num_results/10), self.max_results)

    def get_results_urls(self, url):
        print whoami()
        max = min(self.max_results, int(self.num_results/10))
        self.result_urls = [{'url':url + '&start='+str(10*i) , 'offset':i} for i in range(1, max)]

    def get_case_urls_from_result_url(self, base_url, url, offset):
        print whoami()
        soup_url = base_url + url
        soup = self.get_soup(url)
        h = soup.find('h3', {'class' : 'gs_rt'})
        index = offset + 1
        while h:
            try:
                case_info = {}
                links = h.findAll('a')
                a = links[0]
                case_info['url'] = a['href']
                cites_div = a.findNext('div', {'class' : 'gs_fl'})
                cites = cites_div.findAll('a')
                c = cites[0]
                case_info['cites_url'] = c['href']
                case_info['cites_count'] = c.text.split(" ")[2]
                case_info['index'] = index
                sleep(random.randint(0, self.wait_time))
            except:
                pass
            finally:
                index += 1
                self.case_urls.append(case_info)
                h = h.findNext('h3', {'class' : 'gs_rt'})

    def get_case_text(self, base_url, url, cites_url, cites_count, index):
        print whoami()
        save_dict = locals()
        save_dict.pop('base_url')
        save_dict.pop('self')
        soup = self.get_soup(base_url + url)
        h =  soup.find('h2', {'id':'gs_leaf_hdr_title'})
        save_dict['name'] = h.text
        caseString = ""
        a = h.findNext(['p', 'center', 'blockquote'])
        while a:
            caseString += a.text
            a = a.findNext(['p', 'center', 'blockquote'])
        save_dict['full_text'] = caseString
        save_dict['word_count'] = self.prepare_case_text_to_save(caseString)
        print type(save_dict)
        self.save_to_db(save_dict)

    def prepare_case_text_to_save(self, case_text_string):
       print whoami()
       word_count = Counter(case_text_string.split(" "))
       return word_count
       
    def save_to_db(self, dic):
        print whoami()
        print type(dic)
        for key, item in dic.items():
            print "here is key: "+key
            print type(item)
        self.db.insert(dic, check_keys=False)

 

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', required = True)
    parser.add_argument('-q', required = True)
    parser.add_argument('-m', required = True)
    parser.add_argument('-w', required = True)
    args = vars(parser.parse_args())
    state = args['s']
    search_term = args['q']
    max_results = int(math.ceil(int(args['m'])/10))
    wait_time = int(args['w'])
    mongo = pymongowrapper.MongoDB(db = 'GoogleLaw', collection = search_term + time.strftime('_%m%d%Y_')+search_term)
    research = GoogleLawRequest(state, search_term, mongo, max_results, wait_time)
    research.search()


