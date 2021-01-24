import os
import xml
import json
import trafilatura

from bs4 import BeautifulSoup
from ctypes import c_int64, c_longdouble
from datetime import datetime as dt
from urllib.parse import urljoin, urldefrag
from multiprocessing import Value, Manager
from requests.structures import CaseInsensitiveDict

from . import constants
from .util import MultiProcesser, Q, dequeuer, queuer, dequeue_once, queue_flusher
from .Logger import format_log
from .constants import CrawlResult as CR

STORAGE_METADATA_FOLDER = 'metadata'

def doc_parser(
    qcount, queue, pid, active,
    output_queue, output_qcount, 
    log_queue, log_qcount, 
    num_file, files_size, 
    seen_url_str, fingerprint_set, STORAGE_FOLDER,
):
    doc_q = (qcount, queue, pid)
    log_q = (log_qcount, log_queue, pid)
    doc_output_q = (output_qcount, output_queue, pid + 'DocMgrOutput')
    
    for result, url, doc, headers in dequeuer(*doc_q, active):
        if result == CR.SUCCESS:
            try:
                doc = BeautifulSoup(doc, features='lxml')

            except Exception as e:
                queuer(*log_q, format_log(constants.WARNING, url.url_str, ':%s'%e))
                continue

            else:
                # write doc file
                headers = CaseInsensitiveDict(json.loads(headers))
                extracted = json.loads(trafilatura.extract(str(doc), output_format='json'))
                crawl_time = dt.now()
                fingerprint = extracted['fingerprint']
                
                file_name = '%d_%s'%(dt.timestamp(crawl_time), hash(url.url_str))
                doc_file_path = os.path.join(STORAGE_FOLDER, file_name)
                metadata_file_path = os.path.join(STORAGE_FOLDER, STORAGE_METADATA_FOLDER, file_name+'.json')
                
                if fingerprint in fingerprint_set:
                    queuer(*log_q, format_log(constants.INFO, url.url_str, 'fingerprint repeated'))
                    continue
                else:
                    fingerprint_set[fingerprint] = None
                    with open(doc_file_path, 'w') as f:
                        f.write(extracted.get('raw-text', extracted.get('text', str(doc))))
                
                # extract links
                child_url_strs = []
                for a in doc.find_all('a'):
                    if a.get('href'):
                        url_str = urldefrag(urljoin(url.url_str, a.get('href'))).url
                        child_url_strs.append([url_str, a.text])
                        if url_str not in seen_url_str:
                            seen_url_str[url_str] = None
                            queuer(*doc_output_q, (
                                CR.SUCCESS, 
                                url, 
                                url_str,
                                a.text, 
                            ))
                
                # write metadata file
                title = extracted.get('title', None)
                if title is None or str(title) == '':
                    title = ','.join(x.text for x in doc.findAll('title'))
                
                with open(metadata_file_path, 'w') as f:
                    f.write(json.dumps({
                        'parent_url': url.parent_url_str,
                        'url': url.url_str,
                        'child_urls': child_url_strs,
                        'url_depth': url.depth,
                        'anchor_text': url.anchor_text,
                        'crawl_time': crawl_time.strftime('%Y-%m-%d %H:%M:%S'),
                        'title': title,
                        'fingerprint': fingerprint,
                        'Headers.Age': headers.get('Age', ''),
                        'Headers.Last-Modified': headers.get('Last-Modified', ''),
                        'Headers.Content-Length': headers.get('Content-Length', ''),
                        'Headers.Content-Type': headers.get('Content-Type', ''),
                        }))
                
                update_storage_status(num_file, files_size, doc_file_path)
                
        else:
            queuer(*doc_output_q, (result, url, None, None))

    queue_flusher(*doc_output_q)
    queuer(*log_q, format_log(constants.INFO, 'Doc Parser stopped'))

def update_storage_status(num_file, files_size, file_path):
    with num_file.get_lock():
        num_file.value += 1
    with files_size.get_lock():
        files_size.value += os.path.getsize(file_path)/1024/1024

def create_storage_folder(folder):
    if not os.path.exists(folder):
        os.mkdir(folder)

def init_storage_status(num_file, files_size, folder):
    num_file.value = 0
    files_size.value = 0

    for file in os.listdir(folder):
        path = os.path.join(folder, file)
        if not os.path.islink(path) and not os.path.isdir(path):
            update_storage_status(num_file, files_size, path)

class DocMgr(MultiProcesser):
    def __init__(self, config, logger):
        super().__init__('DocMgr')
        self._config = config
        self._logger = logger
        self._manager = Manager()
        self._seen_url_str = self._manager.dict()
        self._fingerprint_set = self._manager.dict()
        self._output_q = Q('DocMgrOutput')
        self._num_file = Value(c_int64, 0)
        self._files_size = Value(c_longdouble, 0.)
        
        create_storage_folder(self._config.STORAGE_FOLDER)
        create_storage_folder(os.path.join(self._config.STORAGE_FOLDER, STORAGE_METADATA_FOLDER))
        init_storage_status(self._num_file, self._files_size, self._config.STORAGE_FOLDER)
        self.get_storage_status()
    
    def start_doc_parsers(self):
        while len(self._processes) < self._config.MAX_NUMBER_OF_DOC_PARSERS:
            self._start_a_process(target=doc_parser,
                                  kwargs=dict(
                                      num_file=self._num_file, 
                                      files_size=self._files_size,
                                      output_queue=self._output_q.queue,
                                      output_qcount=self._output_q.qcount,
                                      log_queue=self._logger.queue,
                                      log_qcount=self._logger.qcount,
                                      seen_url_str=self._seen_url_str,
                                      fingerprint_set=self._fingerprint_set,
                                      STORAGE_FOLDER=self._config.STORAGE_FOLDER,
                                      ))

    def stop_doc_parsers(self):
        self._stop_all_processes()
        
    def get_parsed(self, n):
        while n>0:
            obj = dequeue_once(self._output_q.qcount, self._output_q.queue, self._output_q._name)
            if obj is not None:
                yield obj
                n -= 1
            else:
                return
    
    def get_storage_status(self):
        self._logger.add(constants.INFO, 'Storage', self._num_file.value, 'files of', self._files_size.value, 'MB')

    @property
    def is_storage_available(self):
        if self._files_size.value >= self._config.STORAGE_SIZE_LIMIT_MB:
            self._logger.add(constants.INFO, 'Storage size full')
            return False
        elif self._num_file.value >= self._config.STORAGE_NUM_DOC_LIMIT:
            self._logger.add(constants.INFO, 'Storage file number full')
            return False
        else:
            return True
    
    @property
    def num_file(self):
        return self._num_file.value
    
    @property
    def files_size(self):
        return self._files_size.value

    