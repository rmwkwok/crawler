import os
import xml
import json

from . import constants
from .util import MultiProcesser, Q, dequeuer, queuer, dequeue_once, queue_flusher
from .Logger import format_log
from .constants import CrawlResult as CR

from bs4 import BeautifulSoup
from ctypes import c_int64, c_longdouble
from datetime import datetime as dt
from urllib.parse import urljoin, urldefrag
from multiprocessing import Value, Manager

def doc_parser(
    qcount, queue, pid, active,
    output_queue, output_qcount, 
    log_queue, log_qcount, 
    num_file, files_size, 
    seen_url_str, STORAGE_FOLDER,
):
    doc_q = (qcount, queue, pid)
    log_q = (log_qcount, log_queue, pid)
    doc_output_q = (output_qcount, output_queue, pid + 'DocMgrOutput')
    
    for result, url, doc in dequeuer(*doc_q, active):
        if result == CR.SUCCESS:
            try:
                doc = BeautifulSoup(doc, features='lxml')

            except Exception as e:
                queuer(*log_q, format_log(constants.WARNING, url.url_str, ':%s'%e))
                continue

            else:
                # write file
                creation_time = dt.now()
                file_name = '%d_%s'%(dt.timestamp(creation_time), hash(url.url_str))
                file_path = os.path.join(STORAGE_FOLDER, file_name)
                
                with open(file_path, 'w') as f:
                    f.write(json.dumps({
                        'metadata': {
                            'url': url.url_str,
                            'url_depth': url.depth,
                            'anchor_text': url.anchor_text,
                            'creation_time': creation_time.strftime('%Y-%m-%d %H:%M:%S'),
                            'title': ','.join(x.text for x in doc.findAll('title')),
                        },
                        'document': str(doc),
                    }))
                update_storage_status(num_file, files_size, file_path)
                    
                # extract links
                for a in doc.find_all('a'):
                    if a.get('href'):
                        url_str = urldefrag(urljoin(url.url_str, a.get('href'))).url
                        if url_str not in seen_url_str:
                            seen_url_str[url_str] = None
                            queuer(*doc_output_q, (
                                CR.SUCCESS, 
                                url, 
                                url_str,
                                a.text, 
                            ))
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
        if not os.path.islink(path):
            update_storage_status(num_file, files_size, path)

class DocMgr(MultiProcesser):
    def __init__(self, config, logger):
        super().__init__('DocMgr')
        self._config = config
        self._logger = logger
        self._manager = Manager()
        self._seen_url_str = self._manager.dict()
        self._output_q = Q('DocMgrOutput')
        self._num_file = Value(c_int64, 0)
        self._files_size = Value(c_longdouble, 0.)
        
        create_storage_folder(self._config.STORAGE_FOLDER)
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

    