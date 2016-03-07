# encoding: utf-8
import errno
import re

from .configuration import Config

import http.server
import socketserver
from urllib.parse import unquote, parse_qs, quote
import hashlib
import logging

import os.path
import os
from ngflush.cachefiles import find_cachefiles

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
    url = unquote(url)
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

    def flush_single_page(self, url, client_address):
        message_parts = []

        url = quote(url)

        cache_key = get_cache_key(url)
        if cache_key is None:
            # cache key not found
            return self.respond(400, "Cache key not provided.")

        cache_key_hash = get_key_hash(cache_key)

        logger.info("%s requested key remove for key (%s) %s" % (client_address, cache_key_hash, cache_key))

        if Config.debug:
            message_parts.append("CACHE_KEY: %s" % hash_from_url(url))
            message_parts.append("CACHE_PATH %s" % path_from_url(url))

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

    def flush_pattern(self, url, client_address):
        """
        Flush all cachefiles whose key match to pattern
        :param parsed_path: query path
        :param client_address: Client address
        :return: None
        """

        parts = parse_qs(url.lstrip("?"))

        print(parts)

        if 'pattern' not in parts:
            return self.respond(400, "Invalid query, pattern missing")

        pattern = ''.join(parts['pattern'])

        content_type = None

        if 'content-type' in parts:
            content_type = ''.join(parts['content-type'])

        if len(pattern) < 2:
            return self.respond(400, "Invalid query, pattern too short")

        logger.info("%s requested key remove for files matching pattern %s" % (
            client_address, pattern))

        files_removed = 0

        try:
            compiled_pattern = re.compile(pattern)
        except re.error:
            return self.respond(400, "Invalid pattern")

        if content_type:
            try:
                content_type = re.compile(content_type)
            except re.error:
                return self.respond(400, "Invalid content-type")

        for file in find_cachefiles(Config.cache_path, compiled_pattern, content_type):
            logger.debug("Flushing file %s" % file)
            flush_path(file)
            files_removed += 1

        return self.respond(200, "%d files matching pattern '%s' removed" % (files_removed, pattern))

    def do_GET(self):
        """
        Handle GET requests
        :return: None
        """
        client_address = self.client_address[0]

        x_forwarded_for = get_case_insensitive(self.headers, 'x-forwarded-for')

        if x_forwarded_for:
            client_address = x_forwarded_for

        if self.path.startswith('/single/'):
            return self.flush_single_page(self.path[8:], client_address)

        elif self.path.startswith('/multiple/'):
            return self.flush_pattern(self.path[10:], client_address)

        return self.respond(404, "Page not found")


def run(port=8000):
    httpd = socketserver.TCPServer(("", port), FlushHandler)
    print("serving at port", port)
    try:
        httpd.serve_forever()
    except:
        print("Closing down")
        httpd.server_close()
