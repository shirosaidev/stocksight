#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""stockprice.py - get stock price from News sources and add to
Elasticsearch.
See README.md or https://github.com/shirosaidev/stocksight
for more information.

Copyright (C) Chris Park 2018
Copyright (C) Allen (Jian Feng) Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""
import argparse
import logging
import sys
import threading
import time
from random import randint

from StockSight.Initializer.ConfigReader import *
from StockSight.Initializer.ElasticSearch import es
from StockSight.EsMap.StockPrice import mapping
from StockSight.StockPriceListener import StockPriceListener


STOCKSIGHT_VERSION = '0.1-b.5'
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

    # set up logging
    logger = logging.getLogger('stocksight')
    logger.setLevel(logging.INFO)
    eslogger = logging.getLogger('elasticsearch')
    eslogger.setLevel(logging.WARNING)
    requestslogger = logging.getLogger('requests')
    requestslogger.setLevel(logging.WARNING)
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
        for symbol in config['symbols']:
            try:
                logger.info('Creating new Price index or using existing ' + symbol)
                es.indices.create(index=config['elasticsearch']['table_prefix']['price']+symbol.lower(),
                                  body=mapping, ignore=[400, 404])

                stockprice = StockPriceListener()

                priceThread = threading.Thread(target=stockprice.get_price,args=(symbol,))
                priceThread.start()

                time.sleep(randint(5,15))

            except Exception as e:
                logger.warning("%s" % e)
                pass
        # get stock price

    except Exception as e:
        logger.warning("Exception: Failed to get stock data caused by: %s" % e)
    except KeyboardInterrupt:
        print("Ctrl-c keyboard interrupt, exiting...")
        sys.exit(0)
