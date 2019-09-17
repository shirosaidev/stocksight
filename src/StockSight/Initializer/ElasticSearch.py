#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Global Elastic Search Handler

Copyright (C) Chris Park 2018-2019
Copyright (C) Allen (Jian Feng) Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

from elasticsearch import Elasticsearch

from StockSight.Initializer.ConfigReader import config

# create instance of elasticsearch
es = Elasticsearch(hosts=[{'host': config['elasticsearch']['host'], 'port': config['elasticsearch']['port']}],
                   http_auth=(config['elasticsearch']['user'], config['elasticsearch']['password']))
