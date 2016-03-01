# encoding: utf-8
import errno

from .configuration import Config

import http.server
import socketserver
from urllib.parse import urlparse
import hashlib
import logging

import os.path
import os

logger = logging.getLogger("ngflush")


class FlushException(Exception):
    pass



def get_key_hash(cache_key):
    """
    Get url for nginx key
    :param url:
    :return:
    """

    cache_key = cache_key.encode("utf-8")

    return hashlib.md5(cache_key).hexdigest()


def get_path(cache_key):
    """
    Get path for given cache_key
    :param cache_key: Cache key
    :return:
    """
    path = str(Config.cache_path + "/")

    levels = Config.cache_levels.split(":")

    a = len(cache_key)
    p = len(cache_key)
    for level in levels:
        p -= int(level)
        path = os.path.join(path, cache_key[p:a])
        a = p

    return os.path.join(path, cache_key)


def check_path(path):
    return os.path.isfile(path)


def flush_path(path):
    """
    Flush given url
    :param path: path to flush
    :return:
    """

    if check_path(path):
        try:
            os.remove(path)
            return
        except IOError as e:
            if e.errno == errno.EACCES:
                logger.error("No permission to remove file %s" % path)
            else:
                logger.exception("Failed to remove key %s" % path)
            raise FlushException("Failed to remove from cache")
    else:
        logger.error("No such file or directory %s" % path)


def get_cache_key(url):
    """
    Get cache key from URL
    :param url:
    :return:
    """
    get_parameter = "&%s=" % Config.get_parameter
    get_parameter2 = "?%s=" % Config.get_parameter
    if get_parameter not in url and get_parameter2 not in url:
        logger.info("get_parameter not found in string")
        return url
    elif get_parameter in url:
        return url.split(get_parameter, 1)[0]
    else:
        return url.split(get_parameter2, 1)[0]


def hash_from_url(url):
    """
    Flush requested address
    :param url:
    :return:
    """
    cache_key = get_cache_key(url)
    if not cache_key:
        return
    return get_key_hash(cache_key)

def path_from_url(url):
    """
    Get path for given key
    :param url:
    :return:
    """
    cache_key = get_cache_key(url)
    if not cache_key:
        return
    return get_path(get_key_hash(cache_key))


def get_case_insensitive(dictionary, key):
    key = key.lower()
    for k,v in dictionary.items():
        if k.lower() == key:
            return v

class FlushHandler(http.server.BaseHTTPRequestHandler):

    def respond(self, error, msg):
        self.send_response(error)
        self.end_headers()
        self.wfile.write(msg.encode("utf-8"))
        return

    def single_page(self, parsed_path, client_address):
        message_parts = []
        cache_key = get_cache_key(parsed_path.query)
        if cache_key is None:
            # cache key not found
            return self.respond(400, "Cache key not provided.")

        cache_key_hash = get_key_hash(cache_key)

        logger.info("%s requested key remove for key (%s) %s" % (client_address, cache_key_hash, cache_key))

        if Config.debug:
            message_parts.append("CACHE_KEY: %s" % hash_from_url(parsed_path.query))
            message_parts.append("CACHE_PATH %s" % path_from_url(parsed_path.query))

        path = get_path(cache_key_hash)
        if not check_path(path):
            return self.respond(404, "Page not found from cache.")

        try:
            flush_path(path)
        except FlushException as e:
            return self.respond(500, str(e))

        message_parts.append("Successfully removed from cache.")

        message_parts.append('')
        message = '\r\n'.join(message_parts)
        return self.respond(200, message)

    def do_GET(self):
        parsed_path = urlparse(self.path)
        client_address = self.client_address[0]

        x_forwarded_for = get_case_insensitive(self.headers, 'x-forwarded-for')

        if x_forwarded_for:
            client_address = x_forwarded_for

        if parsed_path.path == '/single/':
            return self.single_page(parsed_path, client_address)

        return self.respond(404, "Page not found")


def run(port=8000):
    httpd = socketserver.TCPServer(("", port), FlushHandler)
    print("serving at port", port)
    try:
        httpd.serve_forever()
    except:
        print("Closing down")
        httpd.server_close()
