#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Global Config Reader

Copyright (C) Allen (Jian Feng) Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""
import yaml
from definitions import PROJECT_SRC_PATH

config_file = PROJECT_SRC_PATH+'/config.yml'


def load_config(yml_file):
    with open(yml_file) as json_data_file:
        data = yaml.load(json_data_file, yaml.FullLoader)
    return data

config = load_config(config_file)
