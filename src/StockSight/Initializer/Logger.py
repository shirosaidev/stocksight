#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""stockprice.py - get stock price from Yahoo and add to
Elasticsearch.
See README.md or https://github.com/shirosaidev/stocksight
for more information.

Copyright (C) Chris Park 2018
Copyright (C) Allen (Jian Feng) Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

import logging


# set up logging
logger = logging.getLogger('stocksight')
logger.setLevel(logging.INFO)
eslogger = logging.getLogger('elasticsearch')
eslogger.setLevel(logging.WARNING)
requestslogger = logging.getLogger('requests')
requestslogger.setLevel(logging.INFO)
logging.addLevelName(
    logging.INFO, "\033[1;32m%s\033[1;0m"
                  % logging.getLevelName(logging.INFO))
logging.addLevelName(
    logging.WARNING, "\033[1;31m%s\033[1;0m"
                     % logging.getLevelName(logging.WARNING))
logging.addLevelName(
    logging.ERROR, "\033[1;41m%s\033[1;0m"
                   % logging.getLevelName(logging.ERROR))
logging.addLevelName(
    logging.DEBUG, "\033[1;33m%s\033[1;0m"
                   % logging.getLevelName(logging.DEBUG))
logformatter = '%(asctime)s [%(levelname)s][%(name)s] %(message)s'
loglevel = logging.INFO
logging.basicConfig(format=logformatter, level=loglevel)
