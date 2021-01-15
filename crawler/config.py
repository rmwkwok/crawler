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

    MAX_NUMBER_OF_CRAWLERS = 8

    STORAGE_FOLDER = './storage'
    STORAGE_SIZE_LIMIT_MB = 300
    STORAGE_NUM_DOC_LIMIT = 100000

    LOG_SHOW_LOG_LEVEL = 3 #1
    LOG_FOLDER = 'log'
    LOG_SAVE_EVERY_SECOND = 30
