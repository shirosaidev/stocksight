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


import sys
import threading

from StockSight.YahooFinanceListener import *
from StockSight.SeekAlphaListener import *
from StockSight.EsMap.Sentiment import *


STOCKSIGHT_VERSION = '0.1-b.6'
__version__ = STOCKSIGHT_VERSION


if __name__ == '__main__':

    try:
        for symbol in config['symbols']:
            try:
                logger.info('Creating new Sentiment index or using existing ' + symbol)
                es.indices.create(index=config['elasticsearch']['table_prefix']['sentiment']+symbol.lower(), body=mapping, ignore=[400, 404])

                logger.info('NLTK tokens required: ' + str(config['symbols'][symbol]))
                logger.info('NLTK tokens ignored: ' + str(config['sentiment_analyzer']['ignore_words']))

                yahooListener = YahooFinanceListener(symbol)
                yahooThread = threading.Thread(target=yahooListener.execute)
                yahooThread.start()

                seekAlphaListener = SeekAlphaListener(symbol)
                seekAlphaThread = threading.Thread(target=seekAlphaListener.execute)
                seekAlphaThread.start()

                time.sleep(randint(5, 10))
            except Exception as e:
                logger.warning("%s" % e)
                pass

    except KeyboardInterrupt:
        print("Ctrl-c keyboard interrupt, exiting...")
        sys.exit(0)
