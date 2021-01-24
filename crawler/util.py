import time

from ctypes import c_int64, c_bool
from urllib.parse import urlparse
from multiprocessing import Process, Queue, Value, Manager

def get_domain_from_url(url_str):
    parsed = urlparse(url_str)
    return '{scheme}://{netloc}'.format(scheme=parsed.scheme, netloc=parsed.netloc)

class Q:
    def __init__(self, name):
        self._name = name
        self._manager = Manager()
        self._queue = self._manager.Queue()
        self._qcount = Value(c_int64, 0)
    
    def _add_to_queue(self, obj):
        queuer(self._qcount, self._queue, self._name, obj)
        
    def __del__(self):
        queue_flusher(self._qcount, self._queue, self._name)
        print('Flushed', self._name, self._qcount.value, 'items remained', ' '*20)
        
    @property
    def get_queue_size(self):
        return max(0, self._qcount.value)
    
    @property
    def queue(self):
        return self._queue
    
    @property
    def qcount(self):
        return self._qcount

class MultiProcesser(Q):
    def __init__(self, name):
        super().__init__(name)
        self._name = name
        self._processes = dict()
        self._counter = 0
        self._active = Value(c_bool, True)
        
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
                active=self._active,
            ),
        )
        p.start()
        self._counter += 1
        self._processes[pid] = p
        
    def _stop_all_processes(self):
        self._active.value = False
    
    @property
    def num_running_process(self):
        self._check_processes()
        return len(self._processes)
    
    @property
    def num_active_processes(self):
        self._check_processes()
        return len(self._processes)
    
def queuer(qcount, queue, pid, obj):
    queue.put(obj)
    with qcount.get_lock():
        qcount.value += 1
    
def dequeuer(qcount, queue, pid, active):
    while active.value:
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

def queue_flusher(qcount, queue, pid):
    i = REPEAT = 4
    while i > 0:
        i -= 1
        print('flushing', REPEAT, pid, qcount.value, ' '*20, end='\r')
        for _ in range(1000):
            if dequeue_once(qcount, queue, pid) is None:
                break
            else:
                i = REPEAT
        time.sleep(.5)

