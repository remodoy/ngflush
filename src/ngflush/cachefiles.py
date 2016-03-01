import os
import logging

logger = logging.getLogger("ngflush")


class InvalidCacheFile(Exception):
    pass


def get_key_from_file(file, path):
    """
    Get KEY: from cachefile

    KEY: is located in position 145, so value starts from 145 + 5 = 150
    Key value ends with newline.
    :param path: path to file
    :return: KEY from file
    """
    # Check file magic header
    file.seek(0)
    magic = file.read(8)
    if magic != b"\x03\x00\x00\x00\x00\x00\x00\x00":
        raise InvalidCacheFile("Invalid cache file %s" % path)
    file.seek(150)
    return file.readline().decode("utf-8").rstrip('\n')


def find_cachefiles(directory, pattern):
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
                    if pattern.search(get_key_from_file(fd, file_path)) is not None:
                        paths.append(file_path)
            except InvalidCacheFile as e:
                logger.debug(str(e))
    return paths
