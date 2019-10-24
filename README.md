<img src="/docs/stocksight.png?raw=true" alt="stocksight" />

# stocksight
Crowd-sourced stock analyzer and stock predictor using Elasticsearch, Twitter, News headlines and Python natural language processing and sentiment analysis. How much do emotions on Twitter and news headlines affect a stock's price? Let's find out ...

[![License](https://img.shields.io/github/license/shirosaidev/stocksight.svg?label=License&maxAge=86400)](./LICENSE)
[![Release](https://img.shields.io/github/release/shirosaidev/stocksight.svg?label=Release&maxAge=60)](https://github.com/shirosaidev/stocksight/releases/latest)
[![Sponsor Patreon](https://img.shields.io/badge/Sponsor%20%24-Patreon-brightgreen.svg)](https://www.patreon.com/shirosaidev)
[![Donate PayPal](https://img.shields.io/badge/Donate%20%24-PayPal-brightgreen.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=CLF223XAS4W72)

## About
stocksight is a crowd-sourced stock analysis open source software that uses Elasticsearch to store Twitter and news headlines data for stocks. stocksight analyzes the emotions of what the author writes and does sentiment analysis on the text to determine how the author "feels" about a stock. stocksight makes an aggregated analysis of all collected data from all sources.

Each user running stocksight has a unique fingerprint: specific stocks they are following, news sites and twitter users they follow to find information for those stocks. This creates a unique sentiment analysis for each user, based on what data sources they are getting stocksight to search. Users can have the same stocks, but their data sources could vary significantly creating different sentiment analysis for the same stock. stocksight website will allow each user to see other sentiment analysis results from other stocksight user app results and a combined aggregated view of all.

## Stocksight website
https://stocksight.diskoverspace.com
Currently in BETA. Free signup. Once you are registered and login, you will be given a token which you need to add to your stocksight config file to upload your stocksight results to the website.

## Requirements
- Python 3. (tested with Python 3.6.5)
- Elasticsearch 5.
- Kibana 5.
- elasticsearch python module
- nltk python module
- requests python module
- tweepy python module
- beautifulsoup4 python module
- textblob python module
- vaderSentiment python module

### Download

```shell
$ git clone https://github.com/shirosaidev/stocksight.git
$ cd stocksight
```
[Download latest version](https://github.com/shirosaidev/stocksight/releases/latest)

## Screenshot
Stocksight Kibana dashboard
<img src="https://github.com/shirosaidev/stocksight/blob/master/docs/stocksight-dashboard-kibana.png?raw=true" alt="stocksight kibana dashboard" />

## How to use

Install python requirements using pip

`pip install -r requirements.txt`

Create a new twitter application and generate your consumer key and access token. https://developer.twitter.com/en/docs/basics/developer-portal/guides/apps.html
https://developer.twitter.com/en/docs/basics/authentication/guides/access-tokens.html

Copy config.py.sample to config.py

Set elasticsearch settings in config.py for your env

Add twitter consumer key/access token and secrets to config.py

Edit config.py and modify NLTK tokens required/ignored and twitter feeds you want to mine. NLTK tokens required are keywords which must be in tweet before adding it to Elasticsearch (whitelist). NLTK tokens ignored are keywords which if are found in tweet, it will not be added to Elasticsearch (blacklist).

### Examples

Run sentiment.py to create 'stocksight' index in Elasticsearch and start mining and analyzing Tweets using keywords

```sh
$ python sentiment.py -s TSLA -k TSLA,'Elon Musk',Musk,Tesla --debug
```

Start mining and analyzing Tweets from feeds in config using cached user ids from file

```sh
$ python sentiment.py -s TSLA -f twitteruserids.txt --debug
```

Start mining and analyzing News headlines and following headline links and scraping relevant text on landing page

```sh
$ python sentiment.py -s TSLA --followlinks --debug
```

Run stockprice.py to add stock prices to 'stocksight' index in Elasticsearch

```sh
$ python stockprice.py -s TSLA --debug
```

Load 'stocksight' index in Kibana and import export.json file for visuals/dashboard.

### CLI options

```
usage: sentiment.py [-h] [-i INDEX] [-d] -s SYMBOL [-k KEYWORDS] [-a] [-u URL]
                    [-f FILE] [-n] [--frequency FREQUENCY] [--followlinks]
                    [-U] [--noelasticsearch]
                    [--overridetokensreq TOKEN [TOKEN ...]]
                    [--overridetokensignore TOKEN [TOKEN ...]] [-v] [--debug]
                    [-q] [-V]

optional arguments:
  -h, --help            show this help message and exit
  -i INDEX, --index INDEX
                        Index name for Elasticsearch (default: stocksight)
  -d, --delindex        Delete existing Elasticsearch index first
  -s SYMBOL, --symbol SYMBOL
                        Stock symbol you are interesed in searching for,
                        example: TSLA
  -k KEYWORDS, --keywords KEYWORDS
                        Use keywords to search for in Tweets instead of feeds.
                        Separated by comma, case insensitive, spaces are ANDs
                        commas are ORs. Stock symbol from -s will be added to
                        these.Example: 'Elon Musk',Musk,Tesla,SpaceX
  -a, --addtokens       Add nltk tokens required from config to keywords
  -u URL, --url URL     Use twitter users from any links in web page at url
  -f FILE, --file FILE  Use twitter user ids from file
  -n, --newsheadlines   Get news headlines instead of Twitter using stock
                        symbol from -s
  --frequency FREQUENCY
                        How often in seconds to retrieve news headlines
                        (default: 120 sec)
  --followlinks         Follow links on news headlines and scrape relevant
                        text from landing page
  -U, --upload          Upload sentiment to stocksight website (BETA)
  --noelasticsearch     Don't connect or add new docs to Elasticsearch
  --overridetokensreq TOKEN [TOKEN ...]
                        Override nltk required tokens from config, separate
                        with space
  --overridetokensignore TOKEN [TOKEN ...]
                        Override nltk ignore tokens from config, separate with
                        space
  -v, --verbose         Increase output verbosity
  --debug               Debug message output
  -q, --quiet           Run quiet with no message output
  -V, --version         Prints version and exits
  ```
  
  ```
usage: stockprice.py [-h] [-i INDEX] [-d] [-s SYMBOL] [-f FREQUENCY] [-v]
                     [--debug] [-q] [-V]

optional arguments:
  -h, --help            show this help message and exit
  -i INDEX, --index INDEX
                        Index name for Elasticsearch (default: stocksight)
  -d, --delindex        Delete existing Elasticsearch index first
  -s SYMBOL, --symbol SYMBOL
                        Stock symbol to use, example: TSLA
  -f FREQUENCY, --frequency FREQUENCY
                        How often in seconds to retrieve stock data (default:
                        120 sec)
  -v, --verbose         Increase output verbosity
  --debug               Debug message output
  -q, --quiet           Run quiet with no message output
  -V, --version         Prints version and exits
  ```
