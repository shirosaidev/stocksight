#!/bin/bash


sleep 30;

while true
do
    #python stockprice.py -s AMD -i amd &
    python news.sentiment.py &
    sleep 3600
done
