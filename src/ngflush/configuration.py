
import configparser

class Config(object):
    def __init__(self):
        self.cache_path = None
        self.cache_levels = "1:2"
        self.get_parameter = "ngflush"
        self.debug = False


Config = Config()


def strip_value(value):
    return value.strip('"')

def read_config(path="ngflush.ini"):
    config = configparser.ConfigParser()

    config.read(path)

    if 'nginx' not in config.sections():
        raise RuntimeError("Invalid configuration file, nginx section missing")

    nginx = config['nginx']

    if 'cache_path' not in nginx:
        raise RuntimeError("Invalid configuration file, cache_path missing")

    Config.cache_path = strip_value(nginx['cache_path'])

    if 'cache_levels' in nginx:
        Config.cache_levels = strip_value(nginx['cache_levels'])

    if 'flusher' in config:
        flusher = config['flusher']
        if 'get_parameter' in flusher:
            Config.get_parameter = strip_value(flusher['get_parameter'])

        if 'debug' in flusher:
            Config.debug = strip_value(flusher['debug']).lower() == 'true'
