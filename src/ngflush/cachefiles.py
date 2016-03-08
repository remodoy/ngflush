import os
import logging

logger = logging.getLogger("ngflush")


class InvalidCacheFile(Exception):
    pass


class CacheFile(object):
    def __init__(self, file, path):
        self.file = file
        self.path = path
        self.key = None
        self.headers = {}
        self.parse_file()
        self.file.close()

    @classmethod
    def from_file(cls, file, path):
        return CacheFile(file, path)

    def parse_file(self):
        self.file.seek(0)
        magic = self.file.read(8)
        if magic != b"\x03\x00\x00\x00\x00\x00\x00\x00":
            raise InvalidCacheFile("Invalid cache file %s" % self.path)
        self.file.seek(150)
        try:
            self.key = self.file.readline().decode("utf-8", errors="replace").rstrip('\n').rstrip('\r')
            # Read HTTP line
            self.file.readline()
            while True:
                line = self.file.readline()
                if len(line) == 2:
                    break
                line = line.decode("utf-8", errors="replace").rstrip('\n').rstrip('\r')
                if len(line.strip()) == 0:
                    break
                key, value = line.split(":", 1)
                self.headers[key.lower().strip()] = value.strip()
        except Exception as e:
            raise InvalidCacheFile("Invalid cache file %s" % self.path)


def find_cachefiles(directory, pattern, content_type=None):
    """
    Recursively find nginx cachefiles matching given pattern
    :param directory: Base directory for search
    :param pattern: Pattern to search
    :return: List of files
    """
    paths = []
    for path, dirs, files in os.walk(directory):
        for f in files:
            file_path = os.path.join(path, f)
            try:
                with open(file_path, 'rb') as fd:
                    cachefile = CacheFile.from_file(fd, file_path)
                    if pattern.search(cachefile.key) is not None:
                        if content_type:
                            if 'content-type' in cachefile.headers:
                                t = cachefile.headers['content-type']
                                if content_type.search(t) is not None:
                                    paths.append(file_path)
                        else:
                            paths.append(file_path)
            except InvalidCacheFile as e:
                logger.debug(str(e))
    return paths
