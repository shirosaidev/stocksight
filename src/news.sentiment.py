#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""sentiment.py - analyze tweets news sites and their sentiment values to
Elasticsearch.
See README.md or https://github.com/heyqule/stocksight
for more information.

Copyright (C) Allen Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

import argparse
import json
import re
import sys
import time

import nltk
import requests

try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse

# import elasticsearch host, twitter keys and tokens
from NewsHeadlineListener import *


STOCKSIGHT_VERSION = '0.1-b.6'
__version__ = STOCKSIGHT_VERSION

IS_PY3 = sys.version_info >= (3, 0)

if IS_PY3:
    unicode = str



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
            "newsheadline": {
                "properties": {
                    "msg_id": {
                        "type": "string"
                    },
                    "date": {
                        "type": "date"
                    },
                    "location": {
                        "type": "string",
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    },
                    "message": {
                        "type": "string",
                        "fields": {
                            "english": {
                                "type": "string",
                                "analyzer": "english"
                            },
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    },
                    "polarity": {
                        "type": "float"
                    },
                    "subjectivity": {
                        "type": "float"
                    },
                    "sentiment": {
                        "type": "string",
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            }
                        }
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
                url = "https://finance.yahoo.com/quote/%s/?p=%s" % (symbol, symbol)

                logger.info('NLTK tokens required: ' + str(nltk_tokens_required))
                logger.info('NLTK tokens ignored: ' + str(nltk_tokens_ignored))
                logger.info("Scraping news for %s from %s ..." % (symbol, url))

                # create instance of NewsHeadlineListener
                newslistener = NewsHeadlineListener(symbol, url)
            except Exception as e:
                logger.warning("%s" % e)
                pass

    except KeyboardInterrupt:
        print("Ctrl-c keyboard interrupt, exiting...")
        sys.exit(0)