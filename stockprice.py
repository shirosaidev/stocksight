#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""stockprice.py - get stock price from Yahoo and add to
Elasticsearch.
See README.md or https://github.com/shirosaidev/stocksight
for more information.

Copyright (C) Chris Park 2018-2020
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

import time
import requests
import re
import argparse
import logging
import sys
from elasticsearch import Elasticsearch
from random import randint

# import elasticsearch host
from config import elasticsearch_host, elasticsearch_port, elasticsearch_user, elasticsearch_password

from sentiment import STOCKSIGHT_VERSION
__version__ = STOCKSIGHT_VERSION

# url to fetch stock price from, SYMBOL will be replaced with symbol from cli args
url = "https://query1.finance.yahoo.com/v8/finance/chart/SYMBOL?region=US&lang=en-US&includePrePost=false&interval=2m&range=5d&corsDomain=finance.yahoo.com&.tsrc=finance"

# create instance of elasticsearch
es = Elasticsearch(hosts=[{'host': elasticsearch_host, 'port': elasticsearch_port}],
                   http_auth=(elasticsearch_user, elasticsearch_password))

class GetStock:

    def get_price(self, url, symbol):
        import re

        while True:

            logger.info("Grabbing stock data for symbol %s..." % symbol)

            try:

                # add stock symbol to url
                url = re.sub("SYMBOL", symbol, url)
                # get stock data (json) from url
                try:
                    r = requests.get(url)
                    data = r.json()
                except (requests.HTTPError, requests.ConnectionError, requests.ConnectTimeout) as re:
                    logger.error("Exception: exception getting stock data from url caused by %s" % re)
                    raise
                logger.debug(data)
                # build dict to store stock info
                try:
                    D = {}
                    D['symbol'] = symbol
                    D['last'] = data['chart']['result'][0]['indicators']['quote'][0]['close'][-1]
                    if D['last'] is None:
                        D['last'] = data['chart']['result'][0]['indicators']['quote'][0]['close'][-2]
                    D['date'] = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime())  # time now in gmt (utc)
                    try:
                        D['change'] = (data['chart']['result'][0]['indicators']['quote'][0]['close'][-1] -
                                       data['chart']['result'][0]['indicators']['quote'][0]['close'][-2]) / \
                                        data['chart']['result'][0]['indicators']['quote'][0]['close'][-2] * 100
                    except TypeError:
                        D['change'] = (data['chart']['result'][0]['indicators']['quote'][0]['close'][-2] -
                                       data['chart']['result'][0]['indicators']['quote'][0]['close'][-3]) / \
                                      data['chart']['result'][0]['indicators']['quote'][0]['close'][-3] * 100
                        pass
                    D['high'] = data['chart']['result'][0]['indicators']['quote'][0]['high'][-1]
                    if D['high'] is None:
                        D['high'] = data['chart']['result'][0]['indicators']['quote'][0]['high'][-2]
                    D['low'] = data['chart']['result'][0]['indicators']['quote'][0]['low'][-1]
                    if D['low'] is None:
                        D['low'] = data['chart']['result'][0]['indicators']['quote'][0]['low'][-2]
                    D['vol'] = data['chart']['result'][0]['indicators']['quote'][0]['volume'][-1]
                    if D['vol'] is None:
                        D['vol'] = data['chart']['result'][0]['indicators']['quote'][0]['volume'][-2]
                    logger.debug(D)
                except KeyError as e:
                    logger.error("Exception: exception getting stock data caused by %s" % e)
                    raise

                # check before adding to ES
                if D['last'] is not None and D['high'] is not None and D['low'] is not None:
                    logger.info("Adding stock data to Elasticsearch...")
                    # add stock price info to elasticsearch
                    es.index(index=args.index,
                             doc_type="stock",
                             body={"symbol": D['symbol'],
                                   "price_last": D['last'],
                                   "date": D['date'],
                                   "change": D['change'],
                                   "price_high": D['high'],
                                   "price_low": D['low'],
                                   "vol": D['vol']
                                   })
                else:
                    logger.warning("Some stock data had null values, not adding to Elasticsearch")

            except Exception as e:
                logger.error("Exception: can't get stock data, trying again later, reason is %s" % e)
                pass

            logger.info("Will get stock data again in %s sec..." % args.frequency)
            time.sleep(args.frequency)


if __name__ == '__main__':

    # parse cli args
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--index", metavar="INDEX", default="stocksight",
                        help="Index name for Elasticsearch (default: stocksight)")
    parser.add_argument("-d", "--delindex", action="store_true",
                        help="Delete existing Elasticsearch index first")
    parser.add_argument("-s", "--symbol", metavar="SYMBOL",
                        help="Stock symbol to use, example: TSLA")
    parser.add_argument("-f", "--frequency", metavar="FREQUENCY", default=120, type=int,
                        help="How often in seconds to retrieve stock data (default: 120 sec)")
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

    # print banner
    if not args.quiet:
        c = randint(1, 4)
        if c == 1:
            color = '31m'
        elif c == 2:
            color = '32m'
        elif c == 3:
            color = '33m'
        elif c == 4:
            color = '35m'

        banner = """\033[%s
       _                     _                 
     _| |_ _           _   _| |_ _     _   _   
    |   __| |_ ___ ___| |_|   __|_|___| |_| |_ 
    |__   |  _| . |  _| '_|__   | | . |   |  _|
    |_   _|_| |___|___|_,_|_   _|_|_  |_|_|_|  
      |_|                   |_|   |___|                
          :) = +$   :( = -$    v%s
     https://github.com/shirosaidev/stocksight
            \033[0m""" % (color, STOCKSIGHT_VERSION)
        print(banner + '\n')

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

    if args.symbol is None:
        print("No stock symbol, see -h for help.")
        sys.exit(1)

    if args.delindex:
        logger.info('Deleting existing Elasticsearch index ' + args.index)
        es.indices.delete(index=args.index, ignore=[400, 404])

    logger.info('Creating new Elasticsearch index or using existing ' + args.index)
    es.indices.create(index=args.index, body=mappings, ignore=[400, 404])

    # create instance of GetStock
    stockprice = GetStock()

    try:
        # get stock price
        stockprice.get_price(symbol=args.symbol, url=url)
    except Exception as e:
        logger.warning("Exception: Failed to get stock data caused by: %s" % e)
    except KeyboardInterrupt:
        print("Ctrl-c keyboard interrupt, exiting...")
        sys.exit(0)
