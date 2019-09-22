#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Stock Price Mapping

Copyright (C) Chris Park 2018-2019
Copyright (C) Allen (Jian Feng) Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

# set up elasticsearch mappings and create index
mapping = {
    "mappings": {
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
            "price_open": {
                "type": "float"
            },
            "price_close": {
                "type": "float"
            },
            "vol": {
                "type": "integer"
            }
        }
    },
    "settings": {
        "index": {
            "number_of_replicas": "0"
        }
    }
}
