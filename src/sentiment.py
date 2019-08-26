#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""sentiment.py - analyze tweets on Twitter and add
relevant tweets and their sentiment values to
Elasticsearch.
See README.md or https://github.com/shirosaidev/stocksight
for more information.

Copyright (C) Chris Park 2018
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

import argparse
import json
import logging
import re
import sys
import time

import nltk
import requests

try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse
from tweepy.streaming import StreamListener
from tweepy import API, Stream, OAuthHandler, TweepError
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from bs4 import BeautifulSoup
try:
    from elasticsearch5 import Elasticsearch
except ImportError:
    from elasticsearch import Elasticsearch
from random import randint
from datetime import datetime

# import elasticsearch host, twitter keys and tokens
from config import *


STOCKSIGHT_VERSION = '0.1-b.6'
__version__ = STOCKSIGHT_VERSION

IS_PY3 = sys.version_info >= (3, 0)

if IS_PY3:
    unicode = str

# create instance of elasticsearch
es = Elasticsearch(hosts=[{'host': elasticsearch_host, 'port': elasticsearch_port}],
                   http_auth=(elasticsearch_user, elasticsearch_password))

# sentiment text-processing url
sentimentURL = 'http://text-processing.com/api/sentiment/'

# tweet id list
tweet_ids = []

# file to hold twitter user ids
twitter_users_file = './twitteruserids.txt'


class TweetStreamListener(StreamListener):

    # on success
    def on_data(self, data):

        try:
            # decode json
            dict_data = json.loads(data)

            logger.debug(dict_data)

            # clean up tweet text
            #text = unicodedata.normalize(
            #    'NFKD', dict_data["text"]).encode('ascii', 'ignore')
            text = dict_data["text"]
            if text is None:
                logger.info("Tweet has no relevant text, skipping")
                return True

            # grab html links from tweet
            #tweet_urls = re.search("http\S+", text)

            # clean up tweet text more
            text = text.replace("\n", " ")
            text = re.sub(r"http\S+", "", text)
            text = re.sub(r"&.*?;", "", text)
            text = re.sub(r"<.*?>", "", text)
            text = text.replace("RT", "")
            text = text.replace(u"…", "")
            text = text.strip()

            # get date when tweet was created
            created_date = time.strftime(
                '%Y-%m-%dT%H:%M:%S', time.strptime(dict_data['created_at'], '%a %b %d %H:%M:%S +0000 %Y'))

            # store dict_data into vars
            screen_name = str(dict_data.get("user", {}).get("screen_name"))
            location = str(dict_data.get("user", {}).get("location"))
            language = str(dict_data.get("user", {}).get("lang"))
            friends = int(dict_data.get("user", {}).get("friends_count"))
            followers = int(dict_data.get("user", {}).get("followers_count"))
            statuses = int(dict_data.get("user", {}).get("statuses_count"))
            text_filtered = str(text)
            tweetid = int(dict_data.get("id"))
            text_raw = unicode(dict_data.get("text"))

            # output twitter data
            print("\n------------------------------")
            print("Tweet Date: " + created_date)
            print("Screen Name: " + screen_name)
            print("Location: " + location)
            print("Language: " + language)
            print("Friends: " + str(friends))
            print("Followers: " + str(followers))
            print("Statuses: " + str(statuses))
            print("Tweet ID: " + str(tweetid))
            print("Tweet Raw Text: " + text_raw)
            print("Tweet Filtered Text: " + text_filtered)

            # create tokens of words in text using nltk
            text_for_tokens = re.sub(
                r"[\%|\$|\.|\,|\!|\:|\@]|\(|\)|\#|\+|(``)|('')|\?|\-", "", text_filtered)
            tokens = nltk.word_tokenize(text_for_tokens)
            print("NLTK Tokens: " + str(tokens))

            # do some checks before adding to elasticsearch and crawling urls in tweet
            if friends == 0 or \
                            followers == 0 or \
                            statuses == 0 or \
                            text == "" or \
                            tweetid in tweet_ids:
                logger.info("Tweet doesn't meet min requirements, not adding")
                return True

            # check ignored tokens from config
            for t in nltk_tokens_ignored:
                if t in tokens:
                    logger.info("Tweet contains token from ignore list, not adding")
                    return True
            # check required tokens from config
            tokenspass = False
            for t in nltk_tokens_required:
                if t in tokens:
                    tokenspass = True
                    break
            if not tokenspass:
                logger.info("Tweet does not contain token from required list, not adding")
                return True

            # strip out hashtags for language processing
            tweet = re.sub(r"[#|@|\$]\S+", "", text)
            tweet.strip()

            # get sentiment values
            polarity, subjectivity, sentiment = sentiment_analysis(tweet)

            # add tweet_id to list
            tweet_ids.append(dict_data["id"])

            # remove hashtags for elasticsearch
            #text_filtered = re.sub(r"[#|@|\$]\S+", "", text_filtered)

            logger.info("Adding tweet to elasticsearch")
            # add twitter data and sentiment info to elasticsearch
            es.index(index=args.index,
                     doc_type="tweet",
                     body={"author": screen_name,
                           "location": location,
                           "language": language,
                           "friends": friends,
                           "followers": followers,
                           "statuses": statuses,
                           "date": created_date,
                           "message": text_filtered,
                           "tweet_id": tweetid,
                           "polarity": polarity,
                           "subjectivity": subjectivity,
                           "sentiment": sentiment})

            return True

        except Exception as e:
            logger.warning("Exception: exception caused by: %s" % e)
            raise

    # on failure
    def on_error(self, status_code):
        logger.error("Got an error with status code: %s" % status_code)
        return True

    # on timeout
    def on_timeout(self):
        logger.warning("Timeout...")
        return True


class NewsHeadlineListener:
    def __init__(self, url=None, frequency=sentiment_frequency):
        self.url = url
        self.headlines = []
        self.followedlinks = []
        self.frequency = frequency
        self.max_cache = 1000;

        while True:
            new_headlines = self.get_news_headlines(self.url)

            self.cleanup()

            # add any new headlines
            for htext, htext_url in new_headlines:
                if htext not in self.headlines:
                    self.headlines.append(htext)

                    datenow = datetime.utcnow().isoformat()
                    # output news data
                    print("\n------------------------------")
                    print("Date: " + datenow)
                    print("News Headline: " + htext)
                    print("Location (url): " + htext_url)

                    # create tokens of words in text using nltk
                    text_for_tokens = re.sub(
                        r"[\%|\$|\.|\,|\!|\:|\@]|\(|\)|\#|\+|(``)|('')|\?|\-", "", htext)
                    tokens = nltk.word_tokenize(text_for_tokens.lower())
                    print("NLTK Tokens: " + str(tokens))

                    # check ignored tokens from config
                    for t in nltk_tokens_ignored:
                        if t in tokens:
                            logger.info("Text contains token from ignore list, not adding")
                            continue
                    # check required tokens from config
                    tokenspass = False


                    if args.index in nltk_tokens_required:
                        nltk_tokens = nltk_tokens_required[args.index]
                    else:
                        nltk_tokens = nltk_tokens_required['default']

                    for t in nltk_tokens:
                        if t in tokens:
                            tokenspass = True
                            break
                    if not tokenspass:
                        logger.info("Text does not contain token from required list, not adding")
                        continue

                    # get sentiment values
                    polarity, subjectivity, sentiment = sentiment_analysis(htext)

                    logger.info("Adding news headline to elasticsearch")
                    # add news headline data and sentiment info to elasticsearch
                    es.index(index=args.index,
                             doc_type="newsheadline",
                             body={"date": datenow,
                                   "location": htext_url,
                                   "message": htext,
                                   "polarity": polarity,
                                   "subjectivity": subjectivity,
                                   "sentiment": sentiment})

            logger.info("Will get news headlines again in %s sec..." % self.frequency)
            time.sleep(self.frequency)
    def cleanup(self):
        new_headline = []
        new_followlink = []
        if len(self.headlines) > self.max_cache:
            for i in range(self.max_cache / 2, len(self.headlines) - 1):
              new_headline.append(self.headlines[i])

        self.headlines = new_headline

        if len(self.followedlinks) > self.max_cache:
            for i in range(self.max_cache / 2, len(self.followedlinks) - 1):
              new_followlink.append(self.followedlinks[i])

        self.followedlinks = new_followlink


    def get_news_headlines(self, url):

        latestheadlines = []
        latestheadlines_links = []
        parsed_uri = urlparse.urljoin(url, '/')

        try:

            req = requests.get(url)
            html = req.text
            soup = BeautifulSoup(html, 'html.parser')
            html = soup.findAll('h3')
            links = soup.findAll('a')

            logger.debug(html)
            logger.debug(links)

            if html:
                for i in html:
                    latestheadlines.append((i.next.next.next.next, url))
            logger.debug(latestheadlines)

            if args.followlinks:
                if links:
                    for i in links:
                        if '/news/' in i['href']:
                            l = parsed_uri.rstrip('/') + i['href']
                            if l not in self.followedlinks:
                                latestheadlines_links.append(l)
                                self.followedlinks.append(l)
                logger.debug(latestheadlines_links)

                logger.info("Following any new links and grabbing text from page...")

                for linkurl in latestheadlines_links:
                    for p in get_page_text(linkurl):
                        latestheadlines.append((p, linkurl))
                logger.debug(latestheadlines)

        except requests.exceptions.RequestException as re:
            logger.warning("Exception: can't crawl web site (%s)" % re)
            pass

        return latestheadlines


def get_page_text(url):

    max_paragraphs = 10

    try:
        logger.debug(url)
        req = requests.get(url)
        html = req.text
        soup = BeautifulSoup(html, 'html.parser')
        html_p = soup.findAll('p')

        logger.debug(html_p)

        if html_p:
            n = 1
            for i in html_p:
                if n <= max_paragraphs:
                    if i.string is not None:
                        logger.debug(i.string)
                        yield i.string
                n += 1

    except requests.exceptions.RequestException as re:
        logger.warning("Exception: can't crawl web site (%s)" % re)
        pass


def get_sentiment_from_url(text, sentimentURL):
    payload = {'text': text}

    try:
        post = requests.post(sentimentURL, data=payload)
        logger.debug(post.status_code)
        logger.debug(post.text)
    except requests.exceptions.RequestException as re:
        logger.error("Exception: requests exception getting sentiment from url caused by %s" % re)
        raise

    # return None if we are getting throttled or other connection problem
    if post.status_code != 200:
        logger.warning("Can't get sentiment from url caused by %s %s" % (post.status_code, post.text))
        return None

    response = post.json()
    logger.debug(response)

    # neg = response['probability']['neg']
    # neutral = response['probability']['neutral']
    # pos = response['probability']['pos']
    label = response['label']

    # determine if sentiment is positive, negative, or neutral
    if label == "neg":
        sentiment = "negative"
    elif label == "neutral":
        sentiment = "neutral"
    else:
        sentiment = "positive"

    return sentiment


def sentiment_analysis(text):
    """Determine if sentiment is positive, negative, or neutral
    algorithm to figure out if sentiment is positive, negative or neutral
    uses sentiment polarity from TextBlob, VADER Sentiment and
    sentiment from text-processing URL
    could be made better :)
    """

    # pass text into sentiment url
    sentiment_url = get_sentiment_from_url(text, sentimentURL)

    # pass text into TextBlob
    text_tb = TextBlob(text)

    # pass text into VADER Sentiment
    analyzer = SentimentIntensityAnalyzer()
    text_vs = analyzer.polarity_scores(text)

    if sentiment_url is None:
        if text_tb.sentiment.polarity <= 0 and text_vs['compound'] <= -0.5:
            sentiment = "negative"  # very negative
        elif text_tb.sentiment.polarity <= 0 and text_vs['compound'] <= -0.1:
            sentiment = "negative"  # somewhat negative
        elif text_tb.sentiment.polarity == 0 and text_vs['compound'] > -0.1 and text_vs['compound'] < 0.1:
            sentiment = "neutral"
        elif text_tb.sentiment.polarity >= 0 and text_vs['compound'] >= 0.1:
            sentiment = "positive"  # somewhat positive
        elif text_tb.sentiment.polarity > 0 and text_vs['compound'] >= 0.1:
            sentiment = "positive"  # very positive
        else:
            sentiment = "neutral"
    else:
        if text_tb.sentiment.polarity < 0 and text_vs['compound'] <= -0.1 and sentiment_url == "negative":
            sentiment = "negative"  # very negative
        elif text_tb.sentiment.polarity <= 0 and text_vs['compound'] < 0 and sentiment_url == "neutral":
            sentiment = "negative"  # somewhat negative
        elif text_tb.sentiment.polarity >= 0 and text_vs['compound'] > 0 and sentiment_url == "neutral":
            sentiment = "positive"  # somewhat positive
        elif text_tb.sentiment.polarity > 0 and text_vs['compound'] >= 0.1 and sentiment_url == "positive":
            sentiment = "positive"  # very positive
        else:
            sentiment = "neutral"

    # calculate average polarity from TextBlob and VADER
    polarity = (text_tb.sentiment.polarity + text_vs['compound']) / 2
    # output sentiment polarity
    print("Sentiment Polarity: " + str(polarity))

    # output sentiment subjectivity (TextBlob)
    print("Sentiment Subjectivity: " + str(text_tb.sentiment.subjectivity))

    # output sentiment
    print("Sentiment (url): " + str(sentiment_url))
    print("Sentiment (algorithm): " + str(sentiment))

    return polarity, text_tb.sentiment.subjectivity, sentiment


def get_twitter_users_from_url(url):
    twitter_users = []
    logger.info("Grabbing any twitter users from url %s" % url)
    try:
        twitter_urls = ("http://twitter.com/", "http://www.twitter.com/",
                        "https://twitter.com/", "https://www.twitter.com/")
        # req_header = {'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Safari/604.1.38"}
        req = requests.get(url)
        html = req.text
        soup = BeautifulSoup(html, 'html.parser')
        html_links = []
        for link in soup.findAll('a'):
            html_links.append(link.get('href'))
        if html_links:
            for link in html_links:
                # check if twitter_url in link
                parsed_uri = urlparse.urljoin(link, '/')
                # get twitter user name from link and add to list
                if parsed_uri in twitter_urls and "=" not in link and "?" not in link:
                    user = link.split('/')[3]
                    twitter_users.append(u'@' + user)
            logger.debug(twitter_users)
    except requests.exceptions.RequestException as re:
        logger.warning("Requests exception: can't crawl web site caused by: %s" % re)
        pass
    return twitter_users


def get_twitter_users_from_file(file):
    # get twitter user ids from text file
    twitter_users = []
    logger.info("Grabbing any twitter user ids from file %s" % file)
    try:
        f = open(file, "rt", encoding='utf-8')
        for line in f.readlines():
            u = line.strip()
            twitter_users.append(u)
        logger.debug(twitter_users)
        f.close()
    except (IOError, OSError) as e:
        logger.warning("Exception: error opening file caused by: %s" % e)
        pass
    return twitter_users


if __name__ == '__main__':
    # parse cli args
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--index", metavar="INDEX", default="stocksight",
                        help="Index name for Elasticsearch (default: stocksight)")
    parser.add_argument("-d", "--delindex", action="store_true",
                        help="Delete existing Elasticsearch index first")
    parser.add_argument("-k", "--keywords", metavar="KEYWORDS",
                        help="Use keywords to search for in Tweets instead of feeds. "
                             "Separated by comma, case insensitive, spaces are ANDs commas are ORs. "
                             "Example: TSLA,'Elon Musk',Musk,Tesla,SpaceX")
    parser.add_argument("-u", "--url", metavar="URL",
                        help="Use twitter users from any links in web page at url")
    parser.add_argument("-f", "--file", metavar="FILE",
                        help="Use twitter user ids from file")
    parser.add_argument("-n", "--newsheadlines", metavar="SYMBOL",
                        help="Get news headlines instead of Twitter using stock symbol, example: TSLA")
    parser.add_argument("--frequency", metavar="FREQUENCY", default=sentiment_frequency, type=int,
                        help="How often in seconds to retrieve news headlines (default: %d sec)" % sentiment_frequency)
    parser.add_argument("--followlinks", action="store_true",
                        help="Follow links on news headlines and scrape relevant text from landing page")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Increase output verbosity")
    parser.add_argument("--debug", action="store_true",
                        help="Debug message output")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Run quiet with no message output")
    parser.add_argument("-V", "--version", action="version",
                        version="stocksight v%s" % STOCKSIGHT_VERSION,
                        help="Prints version and exits")
    args = parser.parse_args()

    # set up logging
    logger = logging.getLogger('stocksight')
    logger.setLevel(logging.INFO)
    eslogger = logging.getLogger('elasticsearch')
    eslogger.setLevel(logging.WARNING)
    tweepylogger = logging.getLogger('tweepy')
    tweepylogger.setLevel(logging.INFO)
    requestslogger = logging.getLogger('requests')
    requestslogger.setLevel(logging.INFO)
    logging.addLevelName(
        logging.INFO, "\033[1;32m%s\033[1;0m"
                      % logging.getLevelName(logging.INFO))
    logging.addLevelName(
        logging.WARNING, "\033[1;31m%s\033[1;0m"
                         % logging.getLevelName(logging.WARNING))
    logging.addLevelName(
        logging.ERROR, "\033[1;41m%s\033[1;0m"
                       % logging.getLevelName(logging.ERROR))
    logging.addLevelName(
        logging.DEBUG, "\033[1;33m%s\033[1;0m"
                       % logging.getLevelName(logging.DEBUG))
    logformatter = '%(asctime)s [%(levelname)s][%(name)s] %(message)s'
    loglevel = logging.INFO
    logging.basicConfig(format=logformatter, level=loglevel)
    if args.verbose:
        logger.setLevel(logging.INFO)
        eslogger.setLevel(logging.INFO)
        tweepylogger.setLevel(logging.INFO)
        requestslogger.setLevel(logging.INFO)
    if args.debug:
        logger.setLevel(logging.DEBUG)
        eslogger.setLevel(logging.DEBUG)
        tweepylogger.setLevel(logging.DEBUG)
        requestslogger.setLevel(logging.DEBUG)
    if args.quiet:
        logger.disabled = True
        eslogger.disabled = True
        tweepylogger.disabled = True
        requestslogger.disabled = True

    # print banner
    if not args.quiet:
        c = randint(1, 4)
        if c == 1:
            color = '31m'
        elif c == 2:
            color = '32m'
        elif c == 3:
            color = '33m'
        elif c == 4:
            color = '35m'

        banner = """\033[%s
        
             /$$                         /$$                 /$$           /$$         /$$    
            | $$                        | $$                |__/          | $$        | $$    
  /$$$$$$$ /$$$$$$    /$$$$$$   /$$$$$$$| $$   /$$  /$$$$$$$ /$$  /$$$$$$ | $$$$$$$  /$$$$$$  
 /$$_____/|_  $$_/   /$$__  $$ /$$_____/| $$  /$$/ /$$_____/| $$ /$$__  $$| $$__  $$|_  $$_/  
|  $$$$$$   | $$    | $$  \ $$| $$      | $$$$$$/ |  $$$$$$ | $$| $$  \ $$| $$  \ $$  | $$    
 \____  $$  | $$ /$$| $$  | $$| $$      | $$_  $$  \____  $$| $$| $$  | $$| $$  | $$  | $$ /$$
 /$$$$$$$/  |  $$$$/|  $$$$$$/|  $$$$$$$| $$ \  $$ /$$$$$$$/| $$|  $$$$$$$| $$  | $$  |  $$$$/
|_______/    \___/   \______/  \_______/|__/  \__/|_______/ |__/ \____  $$|__/  |__/   \___/  
                                                                 /$$  \ $$                    
                       :) = +$   :( = -$                        |  $$$$$$/                    
                                                                 \______/  v%s
        \033[0m""" % (color, STOCKSIGHT_VERSION)
        print(banner + '\n')

    # set up elasticsearch mappings and create index
    mappings = {
        "mappings": {
            "tweet": {
                "properties": {
                    "author": {
                        "type": "string",
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    },
                    "location": {
                        "type": "string",
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    },
                    "language": {
                        "type": "string",
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    },
                    "friends": {
                        "type": "long"
                    },
                    "followers": {
                        "type": "long"
                    },
                    "statuses": {
                        "type": "long"
                    },
                    "date": {
                        "type": "date"
                    },
                    "message": {
                        "type": "string",
                        "fields": {
                            "english": {
                                "type": "string",
                                "analyzer": "english"
                            },
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    },
                    "tweet_id": {
                        "type": "long"
                    },
                    "polarity": {
                        "type": "float"
                    },
                    "subjectivity": {
                        "type": "float"
                    },
                    "sentiment": {
                        "type": "string",
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    }
                }
            },
            "newsheadline": {
                "properties": {
                    "date": {
                        "type": "date"
                    },
                    "location": {
                        "type": "string",
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    },
                    "message": {
                        "type": "string",
                        "fields": {
                            "english": {
                                "type": "string",
                                "analyzer": "english"
                            },
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    },
                    "polarity": {
                        "type": "float"
                    },
                    "subjectivity": {
                        "type": "float"
                    },
                    "sentiment": {
                        "type": "string",
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    }
                }
            }
        }
    }
    if args.delindex:
        logger.info('Deleting existing Elasticsearch index ' + args.index)
        es.indices.delete(index=args.index, ignore=[400, 404])

    logger.info('Creating new Elasticsearch index or using existing ' + args.index)
    es.indices.create(index=args.index, body=mappings, ignore=[400, 404])

    # are we grabbing news headlines from yahoo finance or twitter
    if args.newsheadlines:
        try:
            url = "https://finance.yahoo.com/quote/%s/?p=%s" % (args.newsheadlines, args.newsheadlines)

            logger.info('NLTK tokens required: ' + str(nltk_tokens_required))
            logger.info('NLTK tokens ignored: ' + str(nltk_tokens_ignored))
            logger.info("Scraping news for %s from %s ..." % (args.newsheadlines, url))

            # create instance of NewsHeadlineListener
            newslistener = NewsHeadlineListener(url, args.frequency)
        except KeyboardInterrupt:
            print("Ctrl-c keyboard interrupt, exiting...")
            sys.exit(0)

    else:
        # create instance of the tweepy tweet stream listener
        tweetlistener = TweetStreamListener()

        # set twitter keys/tokens
        auth = OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = API(auth)

        # create instance of the tweepy stream
        stream = Stream(auth, tweetlistener)

        # grab any twitter users from links in web page at url
        if args.url:
            twitter_users = get_twitter_users_from_url(args.url)
            if len(twitter_users) > 0:
                twitter_feeds = twitter_users
            else:
                logger.info("No twitter users found in links on web page, exiting")
                sys.exit(1)

        # grab twitter users from file
        if args.file:
            twitter_users = get_twitter_users_from_file(args.file)
            if len(twitter_users) > 0:
                useridlist = twitter_users
            else:
                logger.info("No twitter users found in file, exiting")
                sys.exit(1)
        else:
            # build user id list from user names
            logger.info("Looking up Twitter user ids from usernames...")
            useridlist = []
            while True:
                for u in twitter_feeds:
                    try:
                        # get user id from screen name using twitter api
                        user = api.get_user(screen_name=u)
                        uid = int(user.id)
                        if uid not in useridlist:
                            useridlist.append(uid)
                        time.sleep(randint(0, 2))
                    except TweepError as te:
                        # sleep a bit in case twitter suspends us
                        logger.warning("Tweepy exception: twitter api error caused by: %s" % te)
                        logger.info("Sleeping for a random amount of time and retrying...")
                        time.sleep(randint(1,10))
                        continue
                    except KeyboardInterrupt:
                        logger.info("Ctrl-c keyboard interrupt, exiting...")
                        stream.disconnect()
                        sys.exit(0)
                break

            if len(useridlist) > 0:
                logger.info('Writing twitter user ids to text file %s' % twitter_users_file)
                try:
                    f = open(twitter_users_file, "wt", encoding='utf-8')
                    for i in useridlist:
                        line = str(i) + "\n"
                        if type(line) is bytes:
                            line = line.decode('utf-8')
                        f.write(line)
                    f.close()
                except (IOError, OSError) as e:
                    logger.warning("Exception: error writing to file caused by: %s" % e)
                    pass
                except Exception as e:
                    raise

        try:
            # search twitter for keywords
            logger.info('NLTK tokens required: ' + str(nltk_tokens_required))
            logger.info('NLTK tokens ignored: ' + str(nltk_tokens_ignored))
            logger.info('Twitter Feeds: ' + str(twitter_feeds))
            logger.info('Twitter User Ids: ' + str(useridlist))
            logger.info('Twitter keywords: ' + str(args.keywords))
            logger.info('Listening for Tweets (ctrl-c to exit)...')
            if args.keywords is None:
                stream.filter(follow= str(useridlist), languages=['en'])
            else:
                # keywords to search on twitter
                # add keywords to list
                keywords = args.keywords.split(',')

                if args.index in nltk_tokens_required:
                    nltk_tokens = nltk_tokens_required[args.index]
                else:
                    nltk_tokens = nltk_tokens_required['default']

                # add tokens to keywords to list
                for f in nltk_tokens:
                    keywords.append(f.lower())
                stream.filter(track=keywords, languages=['en'])
        except TweepError as te:
            logger.debug("Tweepy Exception: Failed to get tweets caused by: %s" % te)
        except KeyboardInterrupt:
            print("Ctrl-c keyboard interrupt, exiting...")
            stream.disconnect()
            sys.exit(0)
