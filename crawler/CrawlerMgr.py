from . import constants
from .util import MultiProcesser, dequeuer, queuer, queue_flusher
from .Logger import format_log
from .constants import CrawlResult as CR

from datetime import datetime as dt
from urllib.error import HTTPError
from urllib.request import Request, urlopen

def crawler(
    qcount, queue, pid, active, 
    doc_queue, doc_qcount, 
    log_queue, log_qcount, 
    URL_RETRY_HTTP_CODES,
):
    log_q = (log_qcount, log_queue, pid)
    doc_q = (doc_qcount, doc_queue, pid)
    crawler_q = (qcount, queue, pid)
    
    for url in dequeuer(*crawler_q, active):
        try:
            start_time = dt.now()
            doc = urlopen(Request(url=url.url_str)).read()

        except HTTPError as e:
            result = CR.NEED_RETRY if int(e.code) in URL_RETRY_HTTP_CODES else CR.NO_RETRY
            queuer(*doc_q, (result, url, None))
            queuer(*log_q, format_log(constants.INFO, url.url_str, 'Crawler failed: %s'%e))

        except Exception as e:
            queuer(*doc_q, (CR.NO_RETRY, url, None))
            queuer(*log_q, format_log(constants.INFO, url.url_str, 'Crawler failed: %s'%e))

        else:
            queuer(*doc_q, (CR.SUCCESS, url, doc))
            queuer(*log_q, format_log(constants.INFO, url.url_str, 'Crawler done in %d seconds'%(dt.now() - start_time).seconds))

    queue_flusher(*doc_q)
    queuer(*log_q, format_log(constants.INFO, 'Crawler stopped'))
            
class CrawlerMgr(MultiProcesser):
    def __init__(self, config, logger, doc_mgr):
        super().__init__('CrawlerMgr')
        self._config = config
        self._logger = logger
        self._doc_mgr = doc_mgr
        
    def start_crawlers(self):
        while len(self._processes) < self._config.MAX_NUMBER_OF_CRAWLERS:
            self._start_a_process(target=crawler,
                                  kwargs=dict(
                                      log_queue=self._logger.queue,
                                      log_qcount=self._logger.qcount,
                                      doc_queue=self._doc_mgr.queue,
                                      doc_qcount=self._doc_mgr.qcount,
                                      URL_RETRY_HTTP_CODES=self._config.URL_RETRY_HTTP_CODES,
                                      ))
            
    def stop_crawlers(self):
        self._stop_all_processes()
    
    def add_to_queue(self, url):
        self._add_to_queue(url)
        

