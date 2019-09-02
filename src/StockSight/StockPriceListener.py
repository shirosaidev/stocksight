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

from config import weekday_start, weekday_end, hour_start, hour_end, timezone_str
from StockSight.Initializer.Logger import logger
from StockSight.Initializer.ElasticSearch import es

regex = re

class StockPriceListener:

    def get_price(self, symbol):
        url = "https://query1.finance.yahoo.com/v8/finance/chart/SYMBOL?region=US&lang=en-US&includePrePost=false&interval=2m&range=5d&corsDomain=finance.yahoo.com&.tsrc=finance"
        eastern_timezone = timezone(timezone_str)

        if self.isNotLive(eastern_timezone):
            today = datetime.datetime.now(eastern_timezone)
            logger.info("Stock market is not live. Current time: %s" % today.strftime("%Y-%m-%d %H:%M"))
            return self;



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
                es.index(index=symbol,
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

        return self;


    def isNotLive(self, timezone):
        today = datetime.datetime.now(timezone);
        if today.weekday() >= weekday_start and \
           today.weekday() <= weekday_end and \
           today.hour >= hour_start and \
           today.hour <= hour_end:
            return False;

        return True;
