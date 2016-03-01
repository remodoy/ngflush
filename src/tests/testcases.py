import hashlib
from unittest import TestCase, main
from ngflush.configuration import Config
from ngflush.server import get_path, get_cache_key, get_key_hash


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


class TestGetCacheKey(TestCase):

    def setUp(self):
        Config.get_parameter = "testflush"

    def test_get_cache_key_single_argument(self):
        self.assertEquals(get_cache_key("foo?testflush=true"), "foo",
                          "Get cache key failed to parser url without arguments")

    def test_get_cache_key_last_argument(self):
        self.assertEquals(get_cache_key("foo?asdf=foo&testflush=true"), "foo?asdf=foo",
                          "Get cache key failed to parse url with multiple arguments")

    def test_get_cache_with_path(self):
        self.assertEquals(get_cache_key("/asdf/foo?asdf=foo&ngflush=true&testflush=true"),
                          "/asdf/foo?asdf=foo&ngflush=true",
                          "Get cache key failed to parse url with path")

class TestKeyHashing(TestCase):

    def test_hash(self):
        self.assertEqual(get_key_hash("123asdfxd4d",),
                         hashlib.md5(b"123asdfxd4d").hexdigest(),
                         "Hashlib don't return correct md5 value")


if __name__ == '__main__':
    main()
