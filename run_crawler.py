import time
import json
import argparse

from crawler.config import config_desc, Config as config
from crawler.Logger import Logger
from crawler.DocMgr import DocMgr
from crawler.URLMgr import URLMgr
from crawler.Progress import Progress
from crawler.constants import CrawlResult as CR
from crawler.CrawlerMgr import CrawlerMgr

def main():
    # required arguments
    req_args = ['SEED_TARGETS_LIST']
    
    # build arguments parser
    parser = argparse.ArgumentParser()
    for name in dir(config):
        if not name.startswith("__"):
            value = getattr(config, name)
            _type = type(value)
            help_text = config_desc[name]
            
            if _type is list:
                default = ' '.join(map(str, value))
                kwargs = {'type': type(value[0]), 'nargs': '+'}
            else:
                default = str(value)
                kwargs = {'type': _type}
            
            if name in req_args :
                parser.add_argument(name, **dict(kwargs, help='%s (Example: %s)'%(help_text, default)))
            else:
                parser.add_argument('--'+name.lower(), **dict(kwargs, dest=name, help='%s (Default: %s)'%(help_text, default)))

    # retrieve arguments
    args = parser.parse_args()
    for name in vars(args):
        value = getattr(args, name)
        if value is not None:
            setattr(config, name, value)
            
    # build objects
    logger = Logger(config)
    url_mgr = URLMgr(config, logger)
    doc_mgr = DocMgr(config, logger)
    crawler_mgr = CrawlerMgr(config, logger, doc_mgr)
    progress = Progress(config, logger, url_mgr, doc_mgr, crawler_mgr)

    # add seed urls
    with open(config.SEED_TARGETS_LIST, 'r') as f:
        for url_str in f.read().splitlines():
            url_mgr.set(url_str)
    
    # start crawling
    doc_mgr.start_doc_parsers()
    crawler_mgr.start_crawlers()
    while progress.active:
        progress.print()

        for url in url_mgr.get():
            crawler_mgr.add_to_queue(url)

        for result, url, url_str, anchor_text in doc_mgr.get_parsed(n=300):
            if result == CR.SUCCESS:
                url_mgr.set(url_str, anchor_text, parent_URL=url)
            elif result == CR.NEED_RETRY:
                url_mgr.set(url)
            else:
                url_mgr.deactive_url(url)
        
        logger.save_to_disk()
    progress.print(force=True)
    print('\n')
    
    # end crawling
    doc_mgr.stop_doc_parsers()
    crawler_mgr.stop_crawlers()
    while doc_mgr.num_running_process or crawler_mgr.num_running_process:
        time.sleep(.5)
        
    logger.save_to_disk(force=True)
    
if __name__ == '__main__':
    main()
