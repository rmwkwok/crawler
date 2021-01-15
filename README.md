# Crawler (development version)

### Usage example
python3 run_crawler.py seed_targets_list.txt

### seed_targets_list
Example:
> https://en.wikipedia.org/wiki/Machine_learning

### Options
python3 run_crawler.py --help
Option examples:
```
positional arguments:
  SEED_TARGETS_LIST     Default: ./seed_targets_list.txt

optional arguments:
  -h, --help            show this help message and exit
  --log_folder LOG_FOLDER
                        Default: log
  --log_save_every_second LOG_SAVE_EVERY_SECOND
                        Default: 30
  --log_show_log_level LOG_SHOW_LOG_LEVEL
                        Default: 3
  --max_number_of_crawlers MAX_NUMBER_OF_CRAWLERS
                        Default: 8
  --storage_folder STORAGE_FOLDER
                        Default: ./storage
  --storage_num_doc_limit STORAGE_NUM_DOC_LIMIT
                        Default: 100000
  --storage_size_limit_mb STORAGE_SIZE_LIMIT_MB
                        Default: 300
  --url_allowed_domain URL_ALLOWED_DOMAIN
                        Default: ['en.wikipedia.org']
  --url_max_depth URL_MAX_DEPTH
                        Default: 50
  --url_max_length URL_MAX_LENGTH
                        Default: 200
  --url_max_num_slashes URL_MAX_NUM_SLASHES
                        Default: 50
  --url_pattern URL_PATTERN
                        Default: https?://.*\..*/?.*
  --url_retry_http_codes URL_RETRY_HTTP_CODES
                        Default: [500, 502, 503, 504, 522, 524, 408, 429]
  --url_retry_limit URL_RETRY_LIMIT
                        Default: 4
  --url_retry_wait_second URL_RETRY_WAIT_SECOND
                        Default: 60

```

### Brief descriptions of behavior
- Starts N=```MAX_NUMBER_OF_CRAWLERS``` parallel-running crawlers
- Put URLs in ```SEED_TARGETS_LIST``` into crawlers' queue, followed by extracted links from crawled documents
- Crawlers process the URLs in FIFO manner
- When ```LOG_SHOW_LOG_LEVEL```=3, it shows a progress bar like this:

> 0d  170s URL:200|30000 Crawler:8/8 File: 100.0MB(33.3%)|   700(0.7%)
>> **0d  170s**: elapsed time
>>
>> **URL:200|30000**: URLs pending and to be crawled. 
>>
>> A URL will be pending for ```URL_RETRY_WAIT_SECOND``` seconds if it was refused (```URL_RETRY_HTTP_CODES```)
>>
>> **Crawler:8/8**: Running and total possible number of crawlers
>>
>> **File: 100.0MB(33.3%)|   700(0.7%)**: Storage status in terms of size and number of files, and their usage in %

- Keep crawling till all URLs are processed or storage limits (see Options) met

### Output
- a log file under ```LOG_FOLDER```
- crawled docs under ```STORAGE_FOLDER```
- a crawled doc is a json of the following format:
```                
{'metadata': {'url', 'anchor_text', 'url_depth', 'creation_time', 'num_retry'},
 'document': document,
}
               ```
