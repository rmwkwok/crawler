import os
import xml
import json

from . import constants
from .util import MultiProcesser, dequeuer, queuer
from .Logger import format_log
from .constants import CrawlResult as CR

from bs4 import BeautifulSoup
from ctypes import c_int64, c_longdouble
from datetime import datetime as dt
from urllib.parse import urljoin
from multiprocessing import Queue, Value

def doc_parser(qcount, queue, pid, output_q, log_queue, log_qcount, num_file, files_size, STORAGE_FOLDER):
    for result, url, doc in dequeuer(qcount, queue, pid):
        if result == CR.SUCCESS:
            try:
                doc = BeautifulSoup(doc, features='lxml')

            except Exception as e:
                queuer(log_qcount, log_queue, pid, format_log(constants.WARNING, url.url_str, ':%s'%e))
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
                            'anchor_text': url.anchor_text,
                            'url_depth': url.depth,
                            'creation_time': creation_time.strftime('%Y-%m-%d %H:%M:%S'),
                            'num_retry': url.num_retry,
                        },
                        'document': str(doc),
                    }))
                update_storage_status(num_file, files_size, file_path)
                    
                # extract links
                for a in doc.find_all('a'):
                    if a.get('href'):
                        output_q.put((
                            CR.SUCCESS, 
                            url, 
                            urljoin(url.url_str, a.get('href')),
                            a.text, 
                        ))
        else:
            output_q.put((result, url, None, None))

    queuer(log_qcount, log_queue, pid, format_log(constants.INFO, 'Doc Parser stopped'))
    output_q.cancel_join_thread()

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
        self._output_q = Queue()
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
                                      output_q=self._output_q,
                                      log_queue=self._logger.queue,
                                      log_qcount=self._logger.qcount,
                                      STORAGE_FOLDER=self._config.STORAGE_FOLDER,
                                      ))

    def stop_doc_parsers(self):
        self._stop_all_processes()
        
    def get_parsed(self, n):
        while n>0:
            try:
                yield self._output_q.get_nowait()
                n -= 1
            except:
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

    