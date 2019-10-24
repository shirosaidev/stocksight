#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Global Loggers

Copyright (C) Chris Park 2018-2019
Copyright (C) Allen (Jian Feng) Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

import logging
from StockSight.Initializer.ConfigReader import config

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


if config['console_output_mode'] is 'verbose':
    logger.setLevel(logging.INFO)
    eslogger.setLevel(logging.INFO)
    requestslogger.setLevel(logging.INFO)
elif config['console_output_mode'] is 'debug':
    logger.setLevel(logging.DEBUG)
    eslogger.setLevel(logging.DEBUG)
    requestslogger.setLevel(logging.DEBUG)
elif config['console_output_mode'] is 'quiet':
    logger.disabled = True
    eslogger.disabled = True
    requestslogger.disabled = True
