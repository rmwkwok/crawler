from .constants import ShowLogLevel
from datetime import datetime as dt

class Progress:
    def __init__(self, config, logger, url_mgr, doc_mgr, crawler_mgr):
        self._config = config
        self._logger = logger
        self._url_mgr = url_mgr
        self._doc_mgr = doc_mgr
        self._crawler_mgr = crawler_mgr
        self._start_dt = self._logger.start_dt
        self._last_print_time = self._start_dt
        self._can_print = self._config.LOG_SHOW_LOG_LEVEL == ShowLogLevel.NONE
        
    @property
    def active(self):
        return (self._url_mgr.num_URLs\
                or self._crawler_mgr.num_being_crawled)\
                and self._doc_mgr.is_storage_available
    
        
    def print(self, force=False):
        if force or (self._can_print and ((dt.now() - self._last_print_time).seconds >= 1)):
            delta_time = dt.now() - self._start_dt
            crawl_fmt = '{: >%dd}'%(1+int(self._config.MAX_NUMBER_OF_CRAWLERS/10))
            crawl_fmt = 'Crawler:{crawl_fmt}/{crawl_fmt}'.format(crawl_fmt=crawl_fmt)
            message = ['{}d{: >5d}s'.format(delta_time.days, delta_time.seconds),
                       'URL:{: >3d}|{: >3d}'.format(self._url_mgr.num_URLs,
                                                    self._crawler_mgr.num_being_crawled),
                       crawl_fmt.format(
                           self._crawler_mgr.num_active_crawlers, 
                           self._config.MAX_NUMBER_OF_CRAWLERS),
                       'File:{: >6.1f}MB({: >3.1f}%)|{: >6d}({: >3.1f}%)'.format(
                           self._doc_mgr.files_size, 
                           self._doc_mgr.files_size/self._config.STORAGE_SIZE_LIMIT_MB*100, 
                           self._doc_mgr.num_file,
                           self._doc_mgr.num_file/self._config.STORAGE_NUM_DOC_LIMIT*100),
                       '          ',
                      ]
            print(' '.join(message), end='\r')
            self._last_print_time = dt.now()
