#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Seeking Alpha Listener Tests

Copyright (C) Chris Park 2018-2019
Copyright (C) Allen (Jian Feng) Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

import unittest
from StockSight.SeekAlphaListener import *
from StockSight.EsMap.Sentiment import mapping
import time


class SeekAlphaListenerTest(unittest.TestCase):

    symbol = 'amd'

    def setUp(self):
        config['redis']['db'] = 1
        self.mainClass = SeekAlphaListener(self.symbol)

    def tearDown(self):
        rds.flushdb()

    @classmethod
    def setUpClass(cls):
        cls.index_name = "stocksight_sentiment_test_"+cls.symbol
        es.indices.create(index=cls.index_name, body=mapping, ignore=[400, 404])

    @classmethod
    def tearDownClass(cls):
        rds.flushdb()
        es.indices.delete(index=cls.index_name, ignore=[400, 404])

    def test_get_news_headlines(self):
        headlines = self.mainClass.get_news_headlines()
        self.assertGreaterEqual(headlines.__len__(), 1, "Empty Headline / Page returned 403")
        self.assertIsInstance(headlines[0], Article, "Is not an Article")
        self.assertIsNotNone(headlines[0].title, "Title is empty")
        self.assertIsNotNone(headlines[0].url, "URL is empty")
        self.assertIsNotNone(headlines[0].referer_url, "Refer URL is empty")

    #always fails b/c of 403 requests.
    def test_get_news_headlines_with_body(self):
        config['news']['follow_link'] = True
        headlines = self.mainClass.get_news_headlines()
        self.assertGreaterEqual(headlines.__len__(), 1, "Empty Headline / Page returned 403")
        self.assertIsInstance(headlines[0], Article, "Is not an Article")
        self.assertIsNotNone(headlines[0].title, "Title is empty")
        self.assertIsNotNone(headlines[0].url, "URL is empty")
        self.assertNotEqual(headlines[0].referer_url, '', "Refer URL is empty")

        empty_bodies = 0
        for message in headlines:
            if message.body == '':
                empty_bodies += 1

        self.assertAlmostEqual(empty_bodies, 0, None, "There are %s empty bodies in %s headlines" % (empty_bodies, headlines.__len__()), 5)


    def test_execute(self):
        self.mainClass.index_name = self.index_name
        self.mainClass.execute()
        time.sleep(3)
        logs = es.search(index=self.index_name,body="{}")
        message = logs['hits']['hits'][0]['_source']
        self.assertIsNotNone(message['title'], "Title is empty")
        self.assertIsNotNone(message['url'], "URL is empty")
        self.assertNotEqual(message['referer_url'], '', "Refer URL is empty")
        self.assertIsNotNone(message['sentiment'], "Sentiment is empty")
        self.assertIsNotNone(message['polarity'], "Polarity is empty")

if __name__ == '__main__':
    unittest.main()