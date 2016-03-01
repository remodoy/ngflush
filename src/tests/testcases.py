import hashlib
import random
import string
import tempfile
from unittest import TestCase, main
import io
from ngflush.configuration import Config
from ngflush.server import get_path, get_cache_key, get_key_hash
from ngflush.cachefiles import *


class TestGetPath(TestCase):

    def setUp(self):
        Config.cache_path = "/tmp"

    def test_get_path_1_2(self):
        Config.cache_levels = "1:2"
        self.assertTrue(get_path("5od93kid3") == Config.cache_path + "/3/id/5od93kid3",
                        "Get path returns invalid path for level 1:2")

    def test_get_path_1(self):
        Config.cache_levels = "1"
        self.assertTrue(get_path("5od93kid3") == Config.cache_path + "/3/5od93kid3",
                        "Get path returns invalid path for level 1")

    def test_get_path_3_2(self):
        Config.cache_levels = "3:2"
        self.assertTrue(get_path("5od93kid3") == Config.cache_path + "/id3/3k/5od93kid3",
                        "Get path returns invalid path for level 3:2")

    def test_get_path_3_2_3(self):
        Config.cache_levels = "3:2:3"
        self.assertTrue(get_path("5od93kid3") == Config.cache_path + "/id3/3k/od9/5od93kid3",
                        "Get path returns invalid path for level 3:2:3")

class TestGetCacheKey(TestCase):

    def setUp(self):
        Config.get_parameter = "testflush"

    def test_get_cache_key_single_argument(self):
        self.assertEqual(get_cache_key("foo?testflush=true"), "foo",
                                       "Get cache key failed to parser url without arguments")

    def test_get_cache_key_last_argument(self):
        self.assertEqual(get_cache_key("foo?asdf=foo&testflush=true"), "foo?asdf=foo",
                                       "Get cache key failed to parse url with multiple arguments")

    def test_get_cache_with_path(self):
        self.assertEqual(get_cache_key("/asdf/foo?asdf=foo&ngflush=true&testflush=true"),
                                       "/asdf/foo?asdf=foo&ngflush=true",
                                       "Get cache key failed to parse url with path")

class TestKeyHashing(TestCase):

    def test_hash(self):
        self.assertEqual(get_key_hash("123asdfxd4d",),
                         hashlib.md5(b"123asdfxd4d").hexdigest(),
                         "Hashlib don't return correct md5 value")


def create_cachefile(filehandle, prefix):

    path = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(random.randint(4, 10)))
    key = "KEY: %s/%s\n" % (prefix.rstrip('/'), path)

    filehandle.write(b"\x03")
    for i in range(144):
        filehandle.write(b"\x00")
    filehandle.write(key.encode("utf-8"))
    filehandle.flush()
    filehandle.seek(0)


class TestCacheFileParsing(TestCase):

    def setUp(self):
        self.cachefile = io.BytesIO()
        self.cachefile.write(b"\x03" + b"\x00" * 144)
        self.cachefile.write(b"KEY: httptesting.example.com/testing\n")
        self.cachefile.seek(0)

        self.broken_cachefile = io.BytesIO(b"\x00" * 145)

    def test_parsing_invalid_file(self):
        with self.assertRaises(InvalidCacheFile):
            get_key_from_file(self.broken_cachefile, "testing")

    def test_parsing_valid_file(self):
        self.assertEqual(get_key_from_file(self.cachefile, "testing"),
                         "httptesting.example.com/testing",
                         "Invalid key returned from get_key_from_file")


class TestCacheFileFind(TestCase):
    def setUp(self):
        self.base_directory = tempfile.mkdtemp()
        self.subdirs = []
        self.files = []

        for i in range(5):
            self.subdirs.append(tempfile.mkdtemp(dir=self.base_directory))

        for dir in self.subdirs:
            for i in range(5):
                f, path = tempfile.mkstemp(dir=dir, text=False)
                fd = os.fdopen(f, 'r+b')
                create_cachefile(fd, "httptesting.example.com/")
                self.files.append((fd, path))

    def tearDown(self):
        for file in self.files:
            file[0].close()
            os.remove(file[1])

        for dir in self.subdirs:
            os.rmdir(dir)

        os.rmdir(self.base_directory)

    def test_find_cachefiles(self):
        files = find_cachefiles(self.base_directory, 'testing.example.com')
        self.assertEqual(len(files), 25, "Find didn't find all files")

    def test_find_cachefiles_wrong_pattern(self):
        files = find_cachefiles(self.base_directory, 'testingg.example.com')
        self.assertEqual(len(files), 0, "Find shouldn't find files")

if __name__ == '__main__':
    main()
