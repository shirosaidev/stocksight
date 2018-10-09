# stocksight
Stock analyzer and stock predictor using Elasticsearch, Twitter and Python natural language processing and sentiment analysis

## Requirements
- Python 2
- Elasticsearch 5
- elasticsearch python module
- nltk python module
- requests python module
- tweepy python module
- beautifulsoup4 python module
- textblob python module

## How to use

Create a new twitter application and generate your consumer key and access token. https://developer.twitter.com/en/docs/basics/developer-portal/guides/apps.html
https://developer.twitter.com/en/docs/basics/authentication/guides/access-tokens.html

Add consumer key/access token to config.py

Edit config.py and modify NLTK tokens required/ignored and twitter feeds you want to mine. NLTK tokens required are keywords which must be in tweet before adding it to Elasticsearch (whitelist). NLTK tokens ignored are keywords which if found the tweet will not be added to Elasticsearch (blacklist).

Run sentiment.py to create 'sentiment' index in Elasticsearch and start mining and analyzing Tweets

`python sentiment.py`

Load 'sentiment' index in Kibana.

## Usage options

```
usage: sentiment.py [-h] [-i INDEX] [-d] [-k KEYWORDS] [-u URL] [-f FILE] [-v]
                    [--debug] [-q] [-V]

optional arguments:
  -h, --help            show this help message and exit
  -i INDEX, --index INDEX
                        Index name for Elasticsearch (default: stocksight)
  -d, --delindex        Delete existing Elasticsearch index first
  -k KEYWORDS, --keywords KEYWORDS
                        Keywords to search for in Tweets, separated by comma
                        case insensitive, spaces are ANDs commas are ORs
                        example: aapl,'iphone xs review'
  -u URL, --url URL     Use twitter users from any links in web page at url
  -f FILE, --file FILE  Use twitter user ids from file
  -v, --verbose         Increase output verbosity
  --debug               Debug message output
  -q, --quiet           Run quiet with no message output
  -V, --version         Prints version and exits
  ```
