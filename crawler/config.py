class Config:
    SEED_TARGETS_LIST = './seed_targets_list.txt'

    URL_MAX_DEPTH = 50
    URL_MAX_LENGTH = 200
    URL_MAX_NUM_SLASHES = 50
    URL_RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429] #https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#retry-http-codes
    URL_RETRY_LIMIT = 4
    URL_RETRY_WAIT_SECOND = 60
    URL_PATTERN = r'https?://.*\..*/?.*'
    URL_ALLOWED_DOMAIN = ['en.wikipedia.org']
    URL_DISALLOWED_URL = [
        'en.wikipedia.org/wiki/Artificial_Intelligence:',
        'en.wikipedia.org/wiki/Book:',
        'en.wikipedia.org/wiki/Category:',
        'en.wikipedia.org/wiki/File:',
        'en.wikipedia.org/wiki/Help:',
        'en.wikipedia.org/wiki/Portal:',
        'en.wikipedia.org/wiki/Talk:',
        'en.wikipedia.org/wiki/Template:',
        'en.wikipedia.org/wiki/Template_talk:',
        'en.wikipedia.org/wiki/Wikipedia:',
    ]

    MAX_NUMBER_OF_CRAWLERS = 8
    MAX_NUMBER_OF_DOC_PARSERS = 8

    STORAGE_FOLDER = './storage'
    STORAGE_SIZE_LIMIT_MB = 300
    STORAGE_NUM_DOC_LIMIT = 100000

    LOG_SHOW_LOG_LEVEL = 3 #1
    LOG_FOLDER = 'log'
    LOG_SAVE_EVERY_SECOND = 30
    
    BUFFER_SIZE_FOR_CRAWLED_DOC = 100
    BUFFER_SIZE_FOR_CRAWLING_URL = 200000

config_desc = {
    'SEED_TARGETS_LIST': 'A file containing seed URLs one in each line',
    
    'URL_MAX_DEPTH': 'Maximum allowable depth relative to seed',
    'URL_MAX_LENGTH': 'Maximum allowable number of characters in the URL',
    'URL_MAX_NUM_SLASHES': 'Maximum allowable number of slashes in the URL',
    'URL_RETRY_HTTP_CODES': 'HTTP Error Code that is retry-able',
    'URL_RETRY_LIMIT': 'Maximum allowable number of retrial',
    'URL_RETRY_WAIT_SECOND': 'Number of seconds to wait between two retrials',
    'URL_PATTERN': 'URL pattern in regular expression',
    'URL_ALLOWED_DOMAIN': 'A list of domain allowable, separated by space (regex)',
    'URL_DISALLOWED_URL': 'A list of URLs disallowed, separated by space (regex)',
    
    'MAX_NUMBER_OF_CRAWLERS': 'Number of multi-threaded crawlers',
    'MAX_NUMBER_OF_DOC_PARSERS': 'Number of multi-threaded document parsers',
    
    'STORAGE_FOLDER': 'Folder path for storage',
    'STORAGE_SIZE_LIMIT_MB': 'Storage limit in MB excluding metadata, above which the crawlers stop',
    'STORAGE_NUM_DOC_LIMIT': 'Storage limit in number of files, above which the crawlers stop',
    
    'LOG_SHOW_LOG_LEVEL': '0: Show all logs, 1: Show only Info and FATAL, 2: Show only FATAL, 3: Show progress bar',
    'LOG_FOLDER': 'Folder path for logs',
    'LOG_SAVE_EVERY_SECOND': 'Interval of saving logs to disk',
    
    'BUFFER_SIZE_FOR_CRAWLED_DOC': 'Buffer size of for documents in terms of number of documents. If the buffer is too large and the doc parsers are not fast enough to digest them, there can be out-of-memory problem. When buffer is full, crawlers pause crawling',
    'BUFFER_SIZE_FOR_CRAWLING_URL': '''Number of allowable URLs in the crawlers' queue, exceeding which any new URLs will be discarded''',
}
    