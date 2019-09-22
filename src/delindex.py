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

from StockSight.Initializer.ElasticSearch import es
from StockSight.Initializer.Logger import *

STOCKSIGHT_VERSION = '0.2'
__version__ = STOCKSIGHT_VERSION

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--delindex", action="store_true",
                        help="Delete existing Elasticsearch index")
    args = parser.parse_args()

    eslogger = logging.getLogger('elasticsearch')
    eslogger.setLevel(logging.INFO)

    if args.delindex:
        eslogger.info('Deleting existing Elasticsearch index ' + args.delindex)
        es.indices.delete(index=args.index, ignore=[400, 404])
