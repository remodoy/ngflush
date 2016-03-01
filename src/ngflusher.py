#!/usr/bin/env python
# encoding: utf-8


from ngflush import server
from ngflush import configuration
import logging

logger = logging.getLogger("ngflush")

import argparse

if __name__ == '__main__':
    logging.basicConfig()

    parser = argparse.ArgumentParser("ngflush")
    parser.add_argument('-c', '--config', help="Path to config file", default="ngflush.ini")
    args = parser.parse_args()

    configuration.read_config(args.config)

    if configuration.Config.debug:
        print("Debug is on")
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.WARN)

    server.run()
