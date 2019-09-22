<img src="/docs/stocksight.png?raw=true" alt="stocksight" />

# stocksight
Crowd-sourced stock analyzer and stock predictor using Elasticsearch, Twitter, News headlines and Python natural language processing and sentiment analysis. How much do emotions on Twitter and news headlines affect a stock's price? Let's find out ...

[![License](https://img.shields.io/github/license/shirosaidev/stocksight.svg?label=License&maxAge=86400)](./LICENSE)
[![Release](https://img.shields.io/github/release/shirosaidev/stocksight.svg?label=Release&maxAge=60)](https://github.com/shirosaidev/stocksight/releases/latest)

### Authors
Chris Park
[![Sponsor Patreon](https://img.shields.io/badge/Sponsor%20%24-Patreon-brightgreen.svg)](https://www.patreon.com/shirosaidev)
[![Donate PayPal](https://img.shields.io/badge/Donate%20%24-PayPal-brightgreen.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=CLF223XAS4W72)

Allen Jian Feng Xie
[![Donate PayPal](https://img.shields.io/badge/Donate%20%24-PayPal-brightgreen.svg)](https://www.paypal.com/paypalme2/heyqule)

## About
stocksight is a crowd-sourced stock analysis open source software that uses Elasticsearch to store Twitter and news headlines data for stocks. stocksight analyzes the emotions of what the author writes and does sentiment analysis on the text to determine how the author "feels" about a stock. stocksight makes an aggregated analysis of all collected data from all sources.

Each user running stocksight has a unique fingerprint: specific stocks they are following, news sites and twitter users they follow to find information for those stocks. This creates a unique sentiment analysis for each user, based on what data sources they are getting stocksight to search. Users can have the same stocks, but their data sources could vary significantly creating different sentiment analysis for the same stock. stocksight website will allow each user to see other sentiment analysis results from other stocksight user app results and a combined aggregated view of all.

<img src="https://github.com/shirosaidev/stocksight/blob/master/docs/stocksight_diagram.png?raw=true" alt="stocksight diagram" />

### Upgrade From 0.1
Version 0.2 went through an architectural revamp.  You will have to COPY the v0.1 data from Elastic 5.6 to Elastic 7.3 if you wish to retain your previous data.

The ElasticSearch index mappings are also different between two versions. New version records additional data for sentiment and stock prices. Please see "src/StockSight/EsMap" files for details.

Differences:
1. Each symbol have its own set of price and sentiment indexes.
2. Each symbol have its dashbaord in Kibana.
3. Each sentiment record have sentiment value for its title and sentiment value for its message.
    - Title sentiment and message sentiment are no longer mixed together.
4. Stock Price open and close values are also saved in price index.    
    

### Requirement

Install Docker on your system

```shell
$ git clone https://github.com/shirosaidev/stocksight.git
$ cd stocksight
```

### How to setup
- Copy src/config.yml to src/config.yml
- Change settings in config.yml to fit your needs
  - Change ElasticSearch credential if needed
  - Change NLTK analyzer ignore words (see sentiment_analyzer:ignore_words:)
  - Add twitter credential and change the twitter feed
    - Create a new twitter application and generate your consumer key and access token.
    - https://developer.twitter.com/en/docs/basics/developer-portal/guides/apps.html
    - https://developer.twitter.com/en/docs/basics/authentication/guides/access-tokens.html
  - Add desired stock symbol and require words to symbols section (see symbol: tsla)
- Change execution intervals in docker-composer.yml
  - default, 120 seconds for stock price, 3600 seconds for news sentiment listeners
- Run "docker-compose up"
- ???
- Profit

### How to use
The following action require to run in the python3 container.

###### View Kibana Dashboard
http://localhost:5601

###### Adding / Changing Stock Symbols
1. open src/config.yml
2. add stock symbol to symbol section.
3. add required keyword of the symbol.
4. the sentiment and price listeners will pick up the change on their next run.

###### Change Twitter Settings When the Instance Is Running.
1. Update the config.yml
2. Log into python container
3. kill twitter.sentiment.py
4. rerun it with "python twitter.sentiment.py &"

##### Adding new news sentiment listener
1. See SeekAlphaListener and YahooFinanceListener as example.
2. Add your class to news.sentitment.py
4. the sentiment runner will pick up the new listener on its next run.

###### Update Kibana Dashboard Template
1. Make change to your existing template and visualizations.
2. Export them to kibana_export/export.7.3.ndjson
3. Replace symbol with "tmpl" or change the id and index value to match existing ndjson.
4. Run "KIBANA_OVERWRITE=true python import.kibana.py"

###### Delete Elastic Indexes
1. Log into python docker console
2. Run "python delindex.py --delindex {index_name}"

### Tech Stack
- Python 3. (tested with Python 3.6.8 and 3.7.4)
- Elasticsearch 7.3.1.
- Kibana 7.3.1.
- Redis 5
- Python module
    - elasticsearch 
    - nltk
    - requests
    - tweepy
    - beautifulsoup4
    - textblob
    - vaderSentiment
    - pytz
    - redis
    - pyyaml
    - fake-useragent
