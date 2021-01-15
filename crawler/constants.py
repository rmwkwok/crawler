INFO    = 'INFO    :'
FATAL   = 'FATAL   :'
WARNING = 'WARNING :'

class CrawlResult:
    NO_RESULT = -1
    SUCCESS = 0
    NO_RETRY = 1
    NEED_RETRY = 2
    
class ShowLogLevel:
    ALL = 0
    INFO_FATAL = 1
    FATAL = 2
    NONE = 3
    