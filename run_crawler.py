import time
import argparse
from crawler.config import Config as config
from crawler.util import argparse_kwargs

from crawler.Logger import logger
from crawler.DocMgr import DocMgr
from crawler.URLMgr import URLMgr
from crawler.Progress import Progress
from crawler.constants import CrawlResult
from crawler.CrawlerMgr import CrawlerMgr

def main():
    # required arguments
    req_args = ['SEED_TARGETS_LIST']
    
    # build arguments parser
    parser = argparse.ArgumentParser()
    for name in dir(config):
        if not name.startswith("__"):
            kwargs = argparse_kwargs(name, vars(config)[name])
            if name in req_args :
                parser.add_argument(name, **kwargs)
            else:
                parser.add_argument('--'+name.lower(), **dict(kwargs, dest=name))

    # retrieve arguments
    args = parser.parse_args()
    for name in vars(args):
        value = getattr(args, name)
        if value is not None:
            setattr(config, name, value)
            
    # build objects
    logger.set_config(config)
    url_mgr = URLMgr(config)
    doc_mgr = DocMgr(config)
    crawler_mgr = CrawlerMgr(config)
    progress = Progress(config, url_mgr, doc_mgr, crawler_mgr)

    # add seed urls
    with open(config.SEED_TARGETS_LIST, 'r') as f:
        for url_str in f.read().splitlines():
            url_mgr.set(url_str)
    
    # start crawling
    crawler_mgr.start_crawler()
    while progress.active:
        progress.print()

        for url in url_mgr.get():
            crawler_mgr.add_to_queue(url)

        crawl_result, url, doc = crawler_mgr.get_crawled()

        if crawl_result == CrawlResult.NEED_RETRY:
            url_mgr.set(url)
        elif crawl_result == CrawlResult.SUCCESS:
            doc_mgr.new_doc(url, doc)
            for url_str, anchor_text in doc_mgr.extract_links(url, doc):
                progress.print()
                url_mgr.set(url_str, anchor_text, parent_URL=url)
        else:
            time.sleep(1)

        logger.save_to_disk()

    # end crawling
    progress.print(force=True)
    crawler_mgr.stop_crawler()
    logger.save_to_disk(force=True)
    print('\n')
    
if __name__ == '__main__':
    main()
