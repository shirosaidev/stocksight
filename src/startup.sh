#!/bin/bash


sleep 30;

echo "Copy kibana dashboard if they don't exist";
python import.kibana.py

tick_time=900
tick=0
let sentiment_time=900*4
while true
do
    echo "Spawning stock price receiver instance";
    python stockprice.py &
    echo "Will get stock data again in ${tick_time} sec...";
    let tick_mod=tick%4

    if [ $tick_mod -eq 0 ]
    then
        echo "Spawning news sentiment receiver instance";
        python news.sentiment.py &
        echo "Will get sentiment data again in ${sentiment_time} sec...";
        let tick=0;
    fi

    sleep $tick_time
    let tick++
done
