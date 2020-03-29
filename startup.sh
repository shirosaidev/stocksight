#!/bin/bash

echo "*******************************************************"
echo
cat << EndOfBanner   
       _                     _                 
     _| |_ _           _   _| |_ _     _   _   
    |   __| |_ ___ ___| |_|   __|_|___| |_| |_ 
    |__   |  _| . |  _| '_|__   | | . |   |  _|
    |_   _|_| |___|___|_,_|_   _|_|_  |_|_|_|  
      |_|                   |_|   |___|                 
          :) = +$   :( = -$
    GitHub repo https://github.com/shirosaidev/stocksight
    StockSight website https://stocksight.diskoverspace.com    

EndOfBanner

echo "stocksight docker container started"
echo "shell into the container and run python sentiment.py -h"
echo
echo "*******************************************************"

while true; do
    sleep 3600
done