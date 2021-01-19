import os
from . import constants
from .constants import ShowLogLevel
from datetime import datetime as dt
from multiprocessing import Manager

def log_level(args):
    if constants.FATAL in args:
        return ShowLogLevel.FATAL
    elif constants.INFO in args:
        return ShowLogLevel.INFO_FATAL
    else:
        return ShowLogLevel.ALL

class Logger:
    def __init__(self, config):
        self._logger_is_set = False
        self._manager = Manager()
        self._buffer = self._manager.list()
        self._start_dt = dt.now()
        self._last_save_time = self._start_dt
        self.set_config(config)
            
    def set_config(self, config):
        self._config = config
        self._log_file = os.path.join(self._config.LOG_FOLDER, 'log_%d'%dt.timestamp(self._start_dt))
        os.makedirs(self._config.LOG_FOLDER, exist_ok=True)
        
        if not os.path.exists(self._log_file):
            with open(self._log_file, 'w') as f:
                pass
        
        self._logger_is_set = True
            
    def add(self, *args):
        message = dt.now().strftime('%Y-%m-%d %H:%M:%S ') + ' '.join(list(map(str, args)))
        
        if log_level(args) >= self._config.LOG_SHOW_LOG_LEVEL:
            print(message)
            
        self._buffer.append(message)
        
    def save_to_disk(self, force=False):
        if force or ((dt.now() - self._last_save_time).seconds >= self._config.LOG_SAVE_EVERY_SECOND):
            with open(self._log_file, 'a') as f:
                while self.is_buffer_filled:
                    f.write(self._buffer.pop(0)+'\n')
        
    @property
    def is_buffer_filled(self):
        return len(self._buffer)
    
    @property
    def start_dt(self):
        return self._start_dt
