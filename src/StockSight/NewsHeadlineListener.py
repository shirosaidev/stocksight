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
import hashlib
import re
from datetime import datetime


import nltk
from abc import ABC, abstractmethod

try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse

from StockSight.Initializer.ConfigReader import config
from StockSight.Initializer.ElasticSearch import es
from StockSight.Initializer.Redis import rds
from StockSight.Helper.Sentiment import *
from StockSight.Model.Article import *


class NewsHeadlineListener(ABC):
    def __init__(self, news_type, symbol, url=None):
        self.symbol = symbol
        self.url = url
        self.type = news_type
        self.cache_length = 2628000
        self.index_name = config['elasticsearch']['table_prefix']['sentiment']+self.symbol.lower()

    def execute(self):
        logger.info("Scraping news for %s from %s... Start" % (self.symbol, self.type))
        articles = self.get_news_headlines()

        # add any new headlines
        for article_obj in articles:

            md5_hash = hashlib.md5((article_obj.title + article_obj.url).encode()).hexdigest()

            if rds.exists(md5_hash) is 0:

                datenow = datetime.utcnow().isoformat()
                # output news data
                print("\n------------------------------")
                print("Date: " + datenow)
                print("News Headline: " + article_obj.title)
                print("Location (url): " + article_obj.url)

                # create tokens of words in text using nltk
                text_for_tokens = re.sub(
                    r"[\%|\$|\.|\,|\!|\:|\@]|\(|\)|\#|\+|(``)|('')|\?|\-", "", article_obj.title)
                tokens = nltk.word_tokenize(text_for_tokens.lower())
                print("NLTK Tokens: " + str(tokens))

                # check ignored tokens from config
                for t in config['sentiment_analyzer']['ignore_words']:
                    if t in tokens:
                        logger.info("Text contains token from ignore list, not adding")
                        rds.set(md5_hash, 1, self.cache_length)
                        continue

                nltk_tokens = []
                if self.symbol in config['tickers']:
                    nltk_tokens = config['tickers'][self.symbol]

                # check required tokens from config
                tokenspass = False
                for t in nltk_tokens:
                    if t in tokens:
                        tokenspass = True
                        break

                if not tokenspass:
                    logger.info("Text does not contain token from required list, not adding")
                    rds.set(md5_hash, 1, self.cache_length)
                    continue

                # get sentiment values
                polarity, subjectivity, sentiment = sentiment_analysis(article_obj.title + "/n" + article_obj.body)

                logger.info("Adding news headline to elasticsearch")
                # add news headline data and sentiment info to elasticsearch
                es.index(index=self.index_name,
                         doc_type="_doc",
                         body={
                               "msg_id": md5_hash,
                               "date": datenow,
                               "referer_url": article_obj.referer_url,
                               "url": article_obj.url,
                               "title": article_obj.title,
                               "message": article_obj.body,
                               "polarity": polarity,
                               "subjectivity": subjectivity,
                               "sentiment": sentiment
                         })

                rds.set(md5_hash, 1, self.cache_length)

        logger.info("Scraping news for %s from %s... Done" % (self.symbol, self.type))

    @abstractmethod
    def get_news_headlines(self):
        pass

    @abstractmethod
    def get_page_text(self, url):
        pass

    def get_article_with_atag(self, raw_article, parsed_uri):
        a_tag = raw_article.find('a')
        url_link = a_tag.get('href')
        if url_link.find('http') != -1:
            return None
        return Article(a_tag.text, parsed_uri+url_link)

