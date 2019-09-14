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
import re
from datetime import datetime
import time
from random import randint


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

            if rds.exists(article_obj.msg_id) is 0:

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
                        rds.set(article_obj.msg_id, 1, self.cache_length)
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
                    rds.set(article_obj.msg_id, 1, self.cache_length)
                    continue

                # get sentiment values
                polarity, subjectivity, sentiment = sentiment_analysis(article_obj.title, True)
                msg_polarity, msg_subjectivity, msg_sentiment = sentiment_analysis(article_obj.body)

                logger.info("Adding news headline to elasticsearch")
                # add news headline data and sentiment info to elasticsearch
                es.index(index=self.index_name,
                         doc_type="_doc",
                         body={
                               "msg_id": article_obj.msg_id,
                               "date": datenow,
                               "referer_url": article_obj.referer_url,
                               "url": article_obj.url,
                               "title": article_obj.title,
                               "message": article_obj.body,
                               "polarity": polarity,
                               "subjectivity": subjectivity,
                               "sentiment": sentiment,
                               "msg_polarity": msg_polarity,
                               "msg_subjectivity": msg_subjectivity,
                               "msg_sentiment": msg_sentiment
                         })

                rds.set(article_obj.msg_id, 1, self.cache_length)

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
        #ignore 3rd party links
        if url_link.find('http') != -1 and url_link.find(parsed_uri) == -1 :
            return None
        return Article(a_tag.text, self.get_proper_new_body_url(url_link,parsed_uri))

    def get_proper_new_body_url(self, article_url, host):
        if article_url.find('http') != -1:
            news_url = article_url
        else:
            news_url = host[0:-1] + article_url
        return news_url

    def can_process(self, article):
        return article is not None and rds.exists(article.msg_id) is 0

    def get_soup(self, url):
        time.sleep(randint(1,3))
        req = requests.get(self.url)
        html = req.text
        soup = BeautifulSoup(html, 'html.parser')
        return soup
