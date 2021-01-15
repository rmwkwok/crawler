import time
from . import constants
from .Logger import logger
from .constants import CrawlResult
from datetime import datetime as dt
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from multiprocessing import Process, Manager, Queue

STOPCRAWLER = 'STOPCRAWLER'

def crawler(queue, documents):
    while True:
        item = queue.get()
        if item == STOPCRAWLER:
            logger.add(constants.INFO, ':Crawler stopped')
            return
        else:
            url_id, url = item
            start_time = dt.now()
            req = Request(url=url.url_str) 
            try:
                doc = urlopen(req).read() 
                logger.add(constants.INFO, url.url_str, ':Crawler done in %d seconds'%(dt.now() - start_time).seconds)
            except HTTPError as e:
                doc = int(e.code)
                logger.add(constants.INFO, url.url_str, ':Crawler failed: %s'%e)
            except Exception as e:
                doc = None
                logger.add(constants.INFO, url.url_str, ':Crawler failed: %s'%e)

            documents[url_id] = doc

class CrawlerMgr:
    def __init__(self, config):
        self._config = config
        self._manager = Manager()
        self._crawlers = []
        self._queue = Queue()
        self._input = dict()
        self._documents = self._manager.dict()

    def check_crawlers(self):
        self._crawlers = [p for p in self._crawlers if p.is_alive()]
        
    def start_crawler(self):
        while len(self._crawlers) < self._config.MAX_NUMBER_OF_CRAWLERS:
            self._crawlers.append(Process(target=crawler, args=(self._queue, self._documents)))
            self._crawlers[-1].start()
            
    def stop_crawler(self):
        while self._queue.qsize():
            try:
                self._queue.get(False)
            except:
                logger.add(constants.INFO, ':Queue emptied')
                time.sleep(.1)
        
        while len(self._crawlers) > 0:
            self._queue.put(STOPCRAWLER)
            time.sleep(.5)
            self.check_crawlers()
    
    def add_to_queue(self, url):
        self._input[id(url)] = url
        self._queue.put((id(url), url))
        
    def get_crawl_result(self, x):
        if isinstance(x, int):
            if x in self._config.URL_RETRY_HTTP_CODES:
                return CrawlResult.NEED_RETRY
            else:
                return CrawlResult.NO_RETRY
        else:
            return CrawlResult.SUCCESS
        
    def get_crawled(self):
        try:
            key, doc = self._documents.popitem()
        except:
            return CrawlResult.NO_RESULT, None, None
        else:
            url = self._input.pop(key)
            return self.get_crawl_result(doc), url, doc
    
    @property
    def num_being_crawled(self):
        return len(self._input)
    
    @property
    def num_active_crawlers(self):
        self.check_crawlers()
        return len(self._crawlers)
