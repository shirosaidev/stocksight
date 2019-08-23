#!/bin/bash

python sentiment.py -n TSLA --followlinks -i tsla &
python stockprice.py -s TSLA -i tsla &
python sentiment.py -n AMD --followlinks -i amd &
python stockprice.py -s AMD -i amd &