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
import time
import datetime
import re
import requests
from pytz import timezone

from StockSight.Initializer.ConfigReader import *
from StockSight.Initializer.Logger import logger
from StockSight.Initializer.ElasticSearch import es

regex = re


class StockPriceListener:
    def __init__(self):
        self.index_name = None

    def get_price(self, symbol):

        logger.info("Scraping price for %s from Yahoo Finance ..." % symbol)

        if self.index_name is None:
            self.index_name = config['elasticsearch']['table_prefix']['price']+symbol.lower()

        url = "https://query1.finance.yahoo.com/v8/finance/chart/SYMBOL?region=US&lang=en-US&includePrePost=false&interval=2m&range=5d&corsDomain=finance.yahoo.com&.tsrc=finance"

        current_timezone = timezone(config['stock_price']['timezone_str'])

        if config['stock_price']['time_check'] and self.is_not_live(current_timezone):
            today = datetime.datetime.now(current_timezone)
            logger.info("Stock market is not live. Current time: %s" % today.strftime("%Y-%m-%d %H:%M"))
            return self

        logger.info("Grabbing stock data for symbol %s..." % symbol)

        try:

            # add stock symbol to url
            url = regex.sub("SYMBOL", symbol, url)
            # get stock data (json) from url
            try:
                r = requests.get(url)
                data = r.json()
            except (requests.HTTPError, requests.ConnectionError, requests.ConnectTimeout) as re:
                logger.error("Exception: exception getting stock data from url caused by %s" % re)
                raise
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
                                   data['chart']['result'][0]['indicators']['quote'][0]['open'][-1]) / \
                                    data['chart']['result'][0]['indicators']['quote'][0]['open'][-1] * 100
                except TypeError:
                    if data['chart']['result'][0]['indicators']['quote'][0]['close'][-2] is not None and \
                       data['chart']['result'][0]['indicators']['quote'][0]['open'][-2] is not None:
                        D['change'] = (data['chart']['result'][0]['indicators']['quote'][0]['close'][-2] -
                                       data['chart']['result'][0]['indicators']['quote'][0]['open'][-2]) / \
                                      data['chart']['result'][0]['indicators']['quote'][0]['open'][-2] * 100
                    else:
                        D['change'] = 0

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
            except KeyError as e:
                logger.error("Exception: exception getting stock data caused by %s" % e)
                raise

            # check before adding to ES
            if D['last'] is not None and D['high'] is not None and D['low'] is not None:
                logger.info("Adding stock data to Elasticsearch...")
                # add stock price info to elasticsearch
                es.index(index=self.index_name,
                         doc_type="_doc",
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

        logger.info("Scraping price for %s from Yahoo Finance... Done" % symbol)

        return self

    def is_not_live(self, current_timezone):
        today = datetime.datetime.now(current_timezone)
        if config['stock_price']['weekday_start'] <= today.weekday() <= config['stock_price']['weekday_end'] and \
            config['stock_price']['hour_start'] <= today.hour <= config['stock_price']['hour_end']:
            return False

        return True
