#!/bin/bash

sleep 30
python sentiment.py -n TSLA -i tsla &
sleep 1
python stockprice.py -s TSLA -i tsla &
sleep 1
python sentiment.py -n AMD -i amd &
sleep 1
python stockprice.py -s AMD -i amd &


while true
do
    sleep 3600
done
