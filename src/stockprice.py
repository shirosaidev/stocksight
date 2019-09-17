#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""stockprice.py - get stock price from News sources and add to
Elasticsearch.
See README.md or https://github.com/shirosaidev/stocksight
for more information.

Copyright (C) Chris Park 2018-2019
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

from StockSight.Initializer.ElasticSearch import es
from StockSight.Initializer.Logger import *
from StockSight.EsMap.StockPrice import mapping
from StockSight.StockPriceListener import StockPriceListener


STOCKSIGHT_VERSION = '0.1-b.5'
__version__ = STOCKSIGHT_VERSION


if __name__ == '__main__':

    try:
        for symbol in config['symbols']:
            try:
                logger.info('Creating new Price index or using existing ' + symbol)
                es.indices.create(index=config['elasticsearch']['table_prefix']['price']+symbol.lower(),
                                  body=mapping, ignore=[400, 404])

                stockprice = StockPriceListener()

                priceThread = threading.Thread(target=stockprice.get_price,args=(symbol,))
                priceThread.start()

                time.sleep(randint(2,5))

            except Exception as e:
                logger.warning("%s" % e)
                pass
        # get stock price

    except Exception as e:
        logger.warning("Exception: Failed to get stock data caused by: %s" % e)
    except KeyboardInterrupt:
        print("Ctrl-c keyboard interrupt, exiting...")
        sys.exit(0)
