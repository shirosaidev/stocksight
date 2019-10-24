#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Request Randomizer Test

Copyright (C) Chris Park 2018-2019
Copyright (C) Allen (Jian Feng) Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""
import unittest
from StockSight.Helper.RequestRandomizer import RequestRandomizer
from StockSight.Initializer.ConfigReader import config
from StockSight.Initializer.Redis import rds

class RequestRandomizerTest(unittest.TestCase):

    def setUp(self):
        config['redis']['db'] = 1


    def tearDown(self):
        rds.flushdb()

    def test_get_a_proxy(self):
        proxy_ip = RequestRandomizer.get_a_proxy()
        self.assertIn(':', proxy_ip, 'Invalid IP format')

    def test_get_a_proxy_reliability(self):
        for x in range(10):
            proxy_ip = RequestRandomizer.get_a_proxy()
            self.assertIn(':', proxy_ip, ('Invalid IP format at %s' % x))

    def test_get_a_user_agent(self):
        ua = RequestRandomizer.get_a_user_agent()
        self.assertIn('Firefox', ua, ('User agent isn\'t firefox'))



if __name__ == '__main__':
    unittest.main()