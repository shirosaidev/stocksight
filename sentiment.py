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

import sys
import json
import time
import re
import unicodedata
import requests
import nltk
import argparse
import logging
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

# import twitter keys and tokens
from config import *


STOCKSIGHT_VERSION = '0.1-b.1'
__version__ = STOCKSIGHT_VERSION

# create instance of elasticsearch
es = Elasticsearch()

# sentiment text-processing url
sentimentURL = 'http://text-processing.com/api/sentiment/'

# tweet id list
tweet_ids = []

# file to hold twitter user ids
twitter_users_file = './twitteruserids.txt'


class TweetStreamListener(StreamListener):

    # on success
    def on_data(self, data):

        # get sentiment from url
        def getSentiment(tweet, sentimentURL):

            payload = {'text': tweet}

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

        def get_header_text(url):

            try:

                header_text = {'h1': [], 'h2': [], 'title': [], 'subtitle': []}
                # req_header = {'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Safari/604.1.38"}
                req = requests.get(url)
                html = req.text
                soup = BeautifulSoup(html, 'html.parser')
                html_h1 = soup.findAll('h1')
                html_h2 = soup.findAll('h2')
                html_title = soup.findAll('title')
                html_subtitle = soup.findAll('subtitle')

                if html_h1:
                    for i in html_h1:
                        header_text['h1'].append(i.string)
                        logger.debug(header_text['h1'])

                if html_h2:
                    for i in html_h2:
                        header_text['h2'].append(i.string)
                        logger.debug(header_text['h2'])

                if html_title:
                    for i in html_title:
                        header_text['title'].append(i.string)
                        logger.debug(header_text['title'])

                if html_subtitle:
                    for i in html_subtitle:
                        header_text['subtitle'].append(i.string)
                        logger.debug(header_text['subtitle'])

            except Exception as e:
                logger.warning("can't crawl web site (%s)" % e)
                pass

            return

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
            # grab html links from tweet to crawl headers for analysis
            #tweet_urls = re.search("http\S+", text)
            # clean up tweet text more
            text = text.replace("\n", " ")
            text = re.sub(r"http\S+", "", text)
            text = re.sub(r"&.*?;", "", text)
            text = re.sub(r"<.*?>", "", text)
            text = text.replace("RT", "")
            text = text.replace("…", "")
            text = text.strip()

            # get date when tweet was created
            created_date = time.strftime(
                '%Y-%m-%dT%H:%M:%S', time.strptime(dict_data['created_at'], '%a %b %d %H:%M:%S +0000 %Y'))

            # store dict_data into vars
            try:
                screen_name = str(dict_data["user"]["screen_name"])
            except AttributeError:
                screen_name = ""
            try:
                location = str(dict_data["user"]["location"])
            except AttributeError:
                location = ""
            try:
                language = str(dict_data["user"]["lang"])
            except AttributeError:
                language = ""
            try:
                friends = int(dict_data["user"]["friends_count"])
            except AttributeError:
                friends = ""
            try:
                followers = int(dict_data["user"]["followers_count"])
            except AttributeError:
                followers = ""
            try:
                statuses = int(dict_data["user"]["statuses_count"])
            except AttributeError:
                statuses = ""
            try:
                text_filtered = str(text)
            except AttributeError:
                text_filtered = ""
            try:
                tweetid = int(dict_data["id"])
            except AttributeError:
                tweetid = ""
            try:
                text_raw = str(dict_data["text"])
            except AttributeError:
                text_raw = ""

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

            # pass tweet into sentiment url
            sentiment_url = getSentiment(text, sentimentURL)

            # strip out hashtags for language processing
            tweet = re.sub(r"[#|@|\$]\S+", "", text)
            tweet.strip()

            # pass tweet into TextBlob
            tweet_tb = TextBlob(tweet)

            # pass tweet into VADER Sentiment
            analyzer = SentimentIntensityAnalyzer()
            tweet_vs = analyzer.polarity_scores(tweet)

            # determine if sentiment is positive, negative, or neutral
            # algorithm to figure out if sentiment is positive, negative or neutral
            # uses sentiment polarity from TextBlob, VADER Sentiment and
            # sentiment from text-processing URL
            # could be made better :)

            if sentiment_url is None:
                if tweet_tb.sentiment.polarity <= 0 and tweet_vs['compound'] <= -0.5:
                    sentiment = "negative"  # very negative
                elif tweet_tb.sentiment.polarity <= 0 and tweet_vs['compound'] <= -0.1:
                    sentiment = "negative"  # somewhat negative
                elif tweet_tb.sentiment.polarity == 0 and tweet_vs['compound'] > -0.1 and tweet_vs['compound'] < 0.1:
                    sentiment = "neutral"
                elif tweet_tb.sentiment.polarity >= 0 and tweet_vs['compound'] >= 0.1:
                    sentiment = "positive"  # somewhat positive
                elif tweet_tb.sentiment.polarity > 0 and tweet_vs['compound'] >= 0.1:
                    sentiment = "positive"  # very positive
                else:
                    sentiment = "neutral"
            else:
                if tweet_tb.sentiment.polarity < 0 and tweet_vs['compound'] <= -0.1 and sentiment_url == "negative":
                    sentiment = "negative"  # very negative
                elif tweet_tb.sentiment.polarity <= 0 and tweet_vs['compound'] < 0 and sentiment_url == "neutral":
                    sentiment = "negative"  # somewhat negative
                elif tweet_tb.sentiment.polarity >= 0 and tweet_vs['compound'] > 0 and sentiment_url == "neutral":
                    sentiment = "positive"  # somewhat positive
                elif tweet_tb.sentiment.polarity > 0 and tweet_vs['compound'] >= 0.1 and sentiment_url == "positive":
                    sentiment = "positive"  # very positive
                else:
                    sentiment = "neutral"

            # calculate average polarity from TextBlob and VADER
            polarity = (tweet_tb.sentiment.polarity + tweet_vs['compound']) / 2
            # output sentiment polarity
            print("Sentiment Polarity: " + str(polarity))

            # output sentiment subjectivity (TextBlob)
            print("Sentiment Subjectivity: " + str(tweet_tb.sentiment.subjectivity))

            # output sentiment
            print("Sentiment (url): " + str(sentiment_url))
            print("Sentiment (algorithm): " + str(sentiment))

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
                           "subjectivity": tweet_tb.sentiment.subjectivity,
                           "sentiment": sentiment})

            # crawl url using beautifulsoup to grab header text
            #if tweet_urls:
            #    print "crawling urls for header text"
                # crawl up to 2 urls
            #    for x in range(0, 1):
            #        try:
            #            url = tweet_urls.group(x)
            #            logger.info("crawling %s" % url)
            #            get_header_text(url)
            #        except Exception:
            #            pass

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
    except Exception as e:
        raise
    return twitter_users


def get_twitter_users_from_file(file):
    twitter_users = []
    logger.info("Grabbing any twitter users from file %s" % file)
    try:
        f = open(file,"r")
        for line in f.readlines():
            twitter_users.append(str(line.strip()))
        logger.debug(twitter_users)
        f.close()
    except (IOError, OSError) as e:
        logger.warning("Exception: error opening file caused by: %s" % e)
        pass
    except Exception as e:
        raise
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
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Increase output verbosity")
    parser.add_argument("--debug", action="store_true",
                        help="Debug message output")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Run quiet with no message output")
    parser.add_argument("-V", "--version", action="version",
                        version="sharesniffer v%s" % STOCKSIGHT_VERSION,
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
            }
        }
    }
    if args.delindex:
        logger.info('Deleting existing Elasticsearch index ' + args.index)
        es.indices.delete(index=args.index, ignore=[400, 404])

    logger.info('Creating new Elasticsearch index or using existing ' + args.index)
    es.indices.create(index=args.index, body=mappings, ignore=[400, 404])

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
        logger.info("Looking up Twitter user id's from usernames...")
        useridlist = []
        while True:
            for u in twitter_feeds:
                try:
                    # get user id from screen name using twitter api
                    user = api.get_user(screen_name=u)
                    uid = str(user.id).encode('utf-8')
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
                f = open(twitter_users_file, "w")
                for i in useridlist:
                    f.write(i + '\n')
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
            stream.filter(follow=useridlist, languages=['en'])
        else:
            # keywords to search on twitter
            # add keywords to list
            keywords = args.keywords.split(',')
            # add tokens to keywords to list
            for f in nltk_tokens_required:
                keywords.append(f)
            stream.filter(track=keywords, languages=['en'])
    except TweepError as te:
        logger.debug("Tweepy Exception: Failed to get tweets caused by: %s" % te)
    except Exception as e:
        logger.warning("Exception: Failed to get tweets caused by: %s" % e)
    except KeyboardInterrupt:
        print("Ctrl-c keyboard interrupt, exiting...")
        stream.disconnect()
        sys.exit(0)
