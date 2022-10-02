from random import choice

from loguru import logger


def get_proxy():
    return
    urls = [
        'http://login:password@ip:port',
    ]
    proxy_url = choice(urls)
    logger.debug("proxy - {}", proxy_url)
    return proxy_url
