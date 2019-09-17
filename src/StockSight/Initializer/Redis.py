#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Redis Global handler


Copyright (C) Allen (Jian Feng) Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""
import redis
from StockSight.Initializer.ConfigReader import config

rds = redis.Redis(host=str(config['redis']['host']), port=config['redis']['port'], db=config['redis']['db'])
