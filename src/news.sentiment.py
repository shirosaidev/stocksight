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

import argparse
import sys
import threading
import time
from random import randint

from StockSight.YahooFinanceListener import *
from StockSight.SeekAlphaListener import *
from StockSight.EsMap.Sentiment import *


STOCKSIGHT_VERSION = '0.1-b.6'
__version__ = STOCKSIGHT_VERSION


if __name__ == '__main__':
    # parse cli args
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Increase output verbosity")
    parser.add_argument("--debug", action="store_true",
                        help="Debug message output")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Run quiet with no message output")
    parser.add_argument("-V", "--version", action="version",
                        version="stocksight v%s" % STOCKSIGHT_VERSION,
                        help="Prints version and exits")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.INFO)
        eslogger.setLevel(logging.INFO)
        requestslogger.setLevel(logging.INFO)
    if args.debug:
        logger.setLevel(logging.DEBUG)
        eslogger.setLevel(logging.DEBUG)
        requestslogger.setLevel(logging.DEBUG)
    if args.quiet:
        logger.disabled = True
        eslogger.disabled = True
        requestslogger.disabled = True

    try:
        for symbol in config['tickers']:
            try:
                logger.info('Creating new Sentiment index or using existing ' + symbol)
                es.indices.create(index=config['elasticsearch']['table_prefix']['sentiment']+symbol.lower(), body=mapping, ignore=[400, 404])

                logger.info('NLTK tokens required: ' + str(config['tickers'][symbol]))
                logger.info('NLTK tokens ignored: ' + str(config['sentiment_analyzer']['ignore_words']))

                yahooListener = YahooFinanceListener(symbol)
                yahooThread = threading.Thread(target=yahooListener.execute)
                yahooThread.start()

                time.sleep(randint(5,15))
            except Exception as e:
                logger.warning("%s" % e)
                pass

    except KeyboardInterrupt:
        print("Ctrl-c keyboard interrupt, exiting...")
        sys.exit(0)