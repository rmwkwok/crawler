import os
import json
from . import constants
from .Logger import logger
from bs4 import BeautifulSoup
from datetime import datetime as dt
from urllib.parse import urljoin

class DocMgr:
    def __init__(self, config):
        self._config = config
        self.create_storage_folder()
        self.init_storage_status()
        self.get_storage_status()
        
    @property
    def is_storage_available(self):
        if self._files_size >= self._config.STORAGE_SIZE_LIMIT_MB:
            logger.add(constants.INFO, 'Storage size full')
            return False
        elif self._num_file >= self._config.STORAGE_NUM_DOC_LIMIT:
            logger.add(constants.INFO, 'Storage file number full')
            return False
        else:
            return True
    
    @property
    def num_file(self):
        return self._num_file
    
    @property
    def files_size(self):
        return self._files_size
    
    def create_storage_folder(self):
        self._storage_folder = self._config.STORAGE_FOLDER
        if not os.path.exists(self._config.STORAGE_FOLDER):
            os.mkdir(self._config.STORAGE_FOLDER)
    
    def init_storage_status(self):
        file_sizes = [ os.path.getsize(os.path.join(self._config.STORAGE_FOLDER, f))
                          for f in os.listdir(self._config.STORAGE_FOLDER)
                              if not os.path.islink(os.path.join(self._config.STORAGE_FOLDER, f))]
        
        self._num_file = len(file_sizes)
        self._files_size = sum(file_sizes)/1024/1024
        
    def get_storage_status(self):
        logger.add(constants.INFO, 'Storage', self._num_file, 'files of', self._files_size, 'MB')
        
    def update_storage_status(self, file_path):
        self._num_file += 1
        self._files_size += os.path.getsize(file_path)/1024/1024
    
    def new_doc(self, url, document):
        try:
            document = str(BeautifulSoup(document, features='lxml'))
        except:
            logger.add(constants.FATAL, url.url_str, ':Unknown doc format')
            logger.add(str(document))
            
        creation_time = dt.now()
        file_name = '%d_%s'%(dt.timestamp(creation_time), hash(url.url_str))
        
        if self._config.STORAGE_FOLDER != self._storage_folder:
            self.create_storage_folder()
        
        file_path = os.path.join(self._config.STORAGE_FOLDER, file_name)
        with open(file_path, 'w') as f:
            f.write(json.dumps(
                {'metadata': {'url': url.url_str,
                             'anchor_text': url.anchor_text,
                             'url_depth': url.depth,
                             'creation_time': creation_time.strftime('%Y-%m-%d %H:%M:%S'),
                             'num_retry': url.num_retry,
                            },
                'document': document,
               }
            ))
        self.update_storage_status(file_path)
    
    def extract_links(self, url, document):
        try:
            for a in BeautifulSoup(document, features='lxml').find_all("a"):
                if a.get('href'):
                    yield urljoin(url.url_str, a.get('href')), a.text
        except Exception as e:
            logger.add(constants.WARNING, url.url_str, ':Exception %s'%e)
            
