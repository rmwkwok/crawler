from .util import get_domain_from_url
from datetime import datetime as dt

class URL:
    def __init__(self, url_str, idx, anchor_text=None, parent_URL=None):
        self._idx = idx
        self._domain = get_domain_from_url(url_str)
        self._url_str = url_str
        self._num_retry = 0
        self._anchor_text = anchor_text
        self._last_failed_ts = None #timestamp of the last failure
        
        if parent_URL:
            self._depth = parent_URL._depth + 1 #depth relative to seed
        else:
            self._depth = 0
        
    def __str__(self):
        return str((self._idx,
                    self._url_str, 
                    self._depth, 
                    self._num_retry, 
                    self._last_failed_ts,
                   ))
    
    def __repr__(self):
        return self.__str__()
    
    @property
    def idx(self):
        return self._idx
    
    @property
    def robot(self):
        return self._robot
    
    @property
    def depth(self):
        return self._depth
    
    @property
    def url_str(self):
        return self._url_str
    
    @property
    def num_retry(self):
        return self._num_retry
    
    @property
    def anchor_text(self):
        return self._anchor_text
    
    @property
    def last_failed_ts(self):
        return self._last_failed_ts
    
    def failed_once(self):
        self._num_retry += 1
        self._last_failed_ts = dt.timestamp(dt.now())
