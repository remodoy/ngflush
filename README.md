NGFlush
=======

Simple cache flush tool for nginx.


Installation
============

* Install python 3.
* Copy ngflush.ini.sample to /etc/ngflush.ini
* Edit /etc/ngflush.ini, fix cache_path and cache_levels if needed.
* Enable systemd service

```shell

cp systemd/ngflush.service /etc/systemd/system/ngflush.service
systemctl daemon-reload
systemctl enable ngflush.service
systemctl start ngflush.service

```

* Configure Nginx, replace CACHE_KEY with proxy_cache_key value, NORMAL_BACKEND with your backend name and CACHE_NAME with cache name.

```nginx

upstream proxy-flush {
    server localhost:8000    weight=100;

}

map $request_uri $proxy_target {
    "~*[?&]ngflush=true" proxy-flush;
    default NORMAL_BACKEND;
}

#
map $request_uri $use_cache {
    "~*[?&]ngflush=true" off;
    default CACHE_NAME;
}

...

server {
...


location /ngflush/ {
    proxy_pass http://proxy-flush/pattern/
}

location / {
  if ($proxy_target = proxy-flush) {
      rewrite ^(.*)$ /single/CACHE_KEY break;
      set $args ""; # Get rid of duplicate arguments
  }

  ...

  proxy_cache $use_cache;  # Prevent caching responses from ngflush.

  ...
}

...

}
```

* Restart nginx
```shell
nginx -t && nginx -s reload
```


License
=======

The MIT License (MIT)
Copyright (c) 2016, Remod Oy

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.