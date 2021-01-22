import time

from ctypes import c_int64
from urllib.parse import urlparse
from multiprocessing import Process, Queue, Value

def get_domain_from_url(url_str):
    parsed = urlparse(url_str)
    return '{scheme}://{netloc}'.format(scheme=parsed.scheme, netloc=parsed.netloc)

class MultiProcesser:
    def __init__(self, name):
        self._name = name
        self._queue = Queue()
        self._qcount = Value(c_int64, 0)
        self._processes = dict()
        self._counter = 0
        
    def _check_processes(self):
        self._processes = {pid: p for pid, p in self._processes.items() if p.is_alive()}
        
    def _start_a_process(self, target, kwargs):
        pid = '%s-%d'%(self._name, self._counter)
        p = Process(
            target=target, 
            kwargs=dict(
                kwargs, 
                qcount=self._qcount, 
                queue=self._queue, 
                pid=pid,
            ),
        )
        p.start()
        self._counter += 1
        self._processes[pid] = p
        
    def _stop_all_processes(self):
        self._qcount.value = -1000
        while len(self._processes) > 0:
            time.sleep(0.5)
            self._check_processes()
    
    def _add_to_queue(self, obj):
        queuer(self._qcount, self._queue, self._name, obj)
        
    @property
    def get_queue_size(self):
        return max(0, self._qcount.value)
    
    @property
    def num_active_processes(self):
        self._check_processes()
        return len(self._processes)
    
    @property
    def queue(self):
        return self._queue
    
    @property
    def qcount(self):
        return self._qcount
    
def queuer(qcount, queue, pid, obj):
    with qcount.get_lock():
        qcount.value += 1
    queue.put(obj)
    
def dequeuer(qcount, queue, pid):
    while qcount.value >= 0:
        try:
            obj = queue.get_nowait()
        except:
            time.sleep(0.5)
            continue
        else:
            with qcount.get_lock():
                qcount.value -= 1
            yield obj
    
def dequeue_once(qcount, queue, pid):
    try:
        obj = queue.get_nowait()
    except:
        return None
    else:
        with qcount.get_lock():
            qcount.value -= 1
        return obj
