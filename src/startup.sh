#!/bin/bash

#Copyright (C) Allen (Jian Feng) Xie 2019
#stocksight is released under the Apache 2.0 license. See
#LICENSE for the full license text.


#Wait script based on https://github.com/elastic/elasticsearch-py/issues/778#issuecomment-384389668
host='http://elasticsearch:9200'
kibanahost='http://kibana:5601/api/status'

#wait for elastic
until $(curl --output /dev/null --silent --head --fail "$host"); do
    printf '.'
    sleep 5
done

# First wait for ES to start...
response=$(curl $host)
until [ "$response" = "200" ]; do
    response=$(curl --write-out %{http_code} --silent --output /dev/null "$host")
    >&2 echo "Elastic Search is unavailable - sleeping"
    sleep 5
done


# next wait for ES status to turn to Green
health="$(curl -fsSL "$host/_cat/health?h=status")"
health="$(echo "$health" | sed -r 's/^[[:space:]]+|[[:space:]]+$//g')" # trim whitespace (otherwise we'll have "green ")

until [ "$health" = 'green' ] || [ "$health" = 'yellow' ]; do
    health="$(curl -fsSL "$host/_cat/health?h=status")"
    health="$(echo "$health" | sed -r 's/^[[:space:]]+|[[:space:]]+$//g')" # trim whitespace (otherwise we'll have "green ")
    >&2 echo "Elastic Search is not healthy."
    sleep 5
done

# First wait for Kibana to start...
response=$(curl $kibanahost)
until [ "$response" = "200" ]; do
    response=$(curl --write-out %{http_code} --silent --output /dev/null "$kibanahost")
    >&2 echo "Kibana is unavailable - sleeping"
    sleep 5
done

kibana_health="$(curl -fsSL "$kibanahost")"
while [[ "$kibana_health" == *"Kibana server is not ready yet"* ]]; do
    kibana_health="$(curl -fsSL "$kibanahost")"
    >&2 echo "Kibana is not ready yet."
    sleep 5
done

echo "Copy kibana dashboard if they don't exist";
python import.kibana.py &

tick_time=900
tick=0
let sentiment_time=900*4

#echo "Spawning Tweet Sentiment receiver instance";
#python tweet.sentiment.py &

while true
do
    echo "Spawning stock price receiver instance";
    python stockprice.py &
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
