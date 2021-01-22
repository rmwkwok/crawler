import os

from . import constants
from .util import MultiProcesser, queuer, dequeue_once
from .constants import ShowLogLevel

from datetime import datetime as dt

def log_level(args):
    if constants.FATAL in args:
        return ShowLogLevel.FATAL
    elif constants.INFO in args:
        return ShowLogLevel.INFO_FATAL
    else:
        return ShowLogLevel.ALL

def format_log(*args):
    return dt.now().strftime('%Y-%m-%d %H:%M:%S ') + ' '.join(list(map(str, args)))
    
class Logger(MultiProcesser):
    def __init__(self, config):
        super().__init__('Logger')
        self._config = config
        self._buffer = list()
        
        self._start_dt = dt.now()
        self._last_save_time = self._start_dt
        
        self._log_file = os.path.join(self._config.LOG_FOLDER, 'log_%d'%dt.timestamp(self._start_dt))
        os.makedirs(self._config.LOG_FOLDER, exist_ok=True)
        if not os.path.exists(self._log_file):
            with open(self._log_file, 'w') as f:
                pass
        
    def add(self, *args):
        queuer(self._qcount, self._queue, self._name, format_log(*args))
        
    def save_to_disk(self, force=False):
        for _ in range(self._qcount.value):
            message = dequeue_once(self._qcount, self._queue, self._name)
            if message is not None:
                self._buffer.append(message)
                if log_level(message) >= self._config.LOG_SHOW_LOG_LEVEL:
                    print(message)
        
        if force or ((dt.now() - self._last_save_time).seconds >= self._config.LOG_SAVE_EVERY_SECOND):
            with open(self._log_file, 'a') as f:
                f.write('\n'.join(self._buffer)+'\n')
                self._buffer.clear()
                self._last_save_time = dt.now()
                    
    @property
    def start_dt(self):
        return self._start_dt
