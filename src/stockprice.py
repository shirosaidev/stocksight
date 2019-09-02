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
import logging
import sys
import time
import datetime
import re
import requests
from pytz import timezone

from config import symbols
from StockSight.Initializer.ElasticSearch import es
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

    # set up elasticsearch mappings and create index
    mappings = {
        "mappings": {
            "stock": {
                "properties": {
                    "symbol": {
                        "type": "keyword"
                    },
                    "price_last": {
                        "type": "float"
                    },
                    "date": {
                        "type": "date"
                    },
                    "change": {
                        "type": "float"
                    },
                    "price_high": {
                        "type": "float"
                    },
                    "price_low": {
                        "type": "float"
                    },
                    "vol": {
                        "type": "integer"
                    }
                }
            }
        }
    }

    try:
        for symbol in symbols:
            try:
                logger.info('Creating new Elasticsearch index or using existing ' + symbol)
                es.indices.create(index=symbol, body=mappings, ignore=[400, 404])

                stockprice = StockPriceListener()

                stockprice.get_price(symbol=symbol)
            except Exception as e:
                logger.warning("%s" % e)
                pass
        # get stock price

    except Exception as e:
        logger.warning("Exception: Failed to get stock data caused by: %s" % e)
    except KeyboardInterrupt:
        print("Ctrl-c keyboard interrupt, exiting...")
        sys.exit(0)
