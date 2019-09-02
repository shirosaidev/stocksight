#!/bin/bash

#Copyright (C) Allen (Jian Feng) Xie 2019
#stocksight is released under the Apache 2.0 license. See
#LICENSE for the full license text.

echo "Waiting for other dependent instances to spawn... (30 seconds)"
sleep 30;

echo "Copy kibana dashboard if they don't exist";
python import.kibana.py

tick_time=900
tick=0
let sentiment_time=900*4

echo "Spawning Tweet Sentiment receiver instance";
python tweet.sentiment.py &

while true
do
    echo "Spawning stock price receiver instance";
    python stockprice.docker.py &
    echo "Will get stock data again in ${tick_time} sec...";
    let tick_mod=tick%4

    if [ $tick_mod -eq 0 ]
    then
        echo "Spawning News Headline Sentiment receiver instance";
        python news.sentiment.py &
        echo "Will get sentiment data again in ${sentiment_time} sec...";
        let tick=0;
    fi

    sleep $tick_time
    let tick++
done
