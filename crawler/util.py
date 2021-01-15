from urllib.parse import urlparse

def get_domain_from_url(url_str):
    parsed = urlparse(url_str)
    return '{scheme}://{netloc}'.format(scheme=parsed.scheme, netloc=parsed.netloc)

def argparse_kwargs(name, value, help=None):
    _type = type(value)
    if type is list:
        return {'type': type(value[0]),
                'nargs': '+',
                'help': 'Default: {}'.format(' '.join(map(str, value))),
                }
    else:
        return {'type': _type,
                'help': 'Default: {}'.format(value),
                }
