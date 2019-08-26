#!/bin/bash

sleep 30
python sentiment.py -n TSLA --followlinks -i tsla &
sleep 1
python stockprice.py -s TSLA -i tsla &
sleep 1
python sentiment.py -n AMD --followlinks -i amd &
sleep 1
python stockprice.py -s AMD -i amd &


while true
do
    sleep 60
done
