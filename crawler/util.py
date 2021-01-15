from urllib.parse import urlparse

def get_domain_from_url(url_str):
    parsed = urlparse(url_str)
    return '{scheme}://{netloc}'.format(scheme=parsed.scheme, netloc=parsed.netloc)
