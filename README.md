<img src="/docs/stocksight.png?raw=true" alt="stocksight" />

# stocksight
Crowd-sourced stock analyzer and stock predictor using Elasticsearch, Twitter, News headlines and Python natural language processing and sentiment analysis. How much do emotions on Twitter and news headlines affect a stock's price? Let's find out ...

[![License](https://img.shields.io/github/license/shirosaidev/stocksight.svg?label=License&maxAge=86400)](./LICENSE)
[![Release](https://img.shields.io/github/release/shirosaidev/stocksight.svg?label=Release&maxAge=60)](https://github.com/shirosaidev/stocksight/releases/latest)

### Authors
Original Author (Chris Park)
[![Sponsor Patreon](https://img.shields.io/badge/Sponsor%20%24-Patreon-brightgreen.svg)](https://www.patreon.com/shirosaidev)
[![Donate PayPal](https://img.shields.io/badge/Donate%20%24-PayPal-brightgreen.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=CLF223XAS4W72)

Docker and new features author (Allen Jian Feng Xie)
[![Donate PayPal](https://img.shields.io/badge/Donate%20%24-PayPal-brightgreen.svg)](https://www.paypal.com/paypalme2/heyqule)

## About
stocksight is a crowd-sourced stock analysis open source software that uses Elasticsearch to store Twitter and news headlines data for stocks. stocksight analyzes the emotions of what the author writes and does sentiment analysis on the text to determine how the author "feels" about a stock. stocksight makes an aggregated analysis of all collected data from all sources.

Each user running stocksight has a unique fingerprint: specific stocks they are following, news sites and twitter users they follow to find information for those stocks. This creates a unique sentiment analysis for each user, based on what data sources they are getting stocksight to search. Users can have the same stocks, but their data sources could vary significantly creating different sentiment analysis for the same stock. stocksight website will allow each user to see other sentiment analysis results from other stocksight user app results and a combined aggregated view of all.

### Requirement

Install Docker on your system

```shell
$ git clone https://github.com/heyqule/stocksight.git
$ cd stocksight
```

### How to setup
- Copy src/config.yml to src/config.yml
- Change settings in config.yml to fit your needs
  - Change ElasticSearch credential (elasticuser:user)
  - Change analyzer ignore words (sentiment_analyzer:ignore_words)
  - If you want to run twitter analyzer, change the setting in twitter section
    - Uncomment ""#python tweet.sentiment.py &" in src/startup.sh
  - Add desired stock symbol and require words to symbols section (symbol: tsla)
- Change run interval in docker-composer.yml
  - default, 900 seconds for stock price, 3600 seconds for news crawler
- Run "docker-compose up"
- ???
- Profit

### How to use
The following action require to run in the python3 container.

###### Delete Elastic Indexes
1. Log into python docker console
2. Run "python delindex.py --delindex {index_name}"

###### Update Kibana Dashboard Template
1. Make change to your existing template and visualizations.
2. Export them to kibana_export/export.7.3.ndjson
3. Replace symbol with "tmpl" or change the id and index value to match existing ndjson.
4. Run "KIBANA_OVERWRITE=true python import.kibana.py"

### Tech Stack
- Python 3. (tested with Python 3.6.8 and 3.7.4)
- Elasticsearch 7.3.1.
- Kibana 7.3.1.
- elasticsearch python module
- nltk python module
- requests python module
- tweepy python module
- beautifulsoup4 python module
- textblob python module
- vaderSentiment python module
- pytz
- redis
- pyyaml
