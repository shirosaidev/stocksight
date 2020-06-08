#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""sentiment.py - analyze tweets on Twitter and add
relevant tweets and their sentiment values to
Elasticsearch.
See README.md or https://github.com/shirosaidev/stocksight
for more information.

Copyright (C) Chris Park 2018-2020
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

import sys
import json
import time
import re
import requests
import nltk
import argparse
import logging
import string
try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse
from tweepy.streaming import StreamListener
from tweepy import API, Stream, OAuthHandler, TweepError
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch
from random import randint, randrange
from datetime import datetime
from newspaper import Article, ArticleException

# import elasticsearch host, twitter keys and tokens
from config import *


STOCKSIGHT_VERSION = '0.1-b.12'
__version__ = STOCKSIGHT_VERSION

IS_PY3 = sys.version_info >= (3, 0)

if not IS_PY3:
    print("Sorry, stocksight requires Python 3.")
    sys.exit(1)

# sentiment text-processing url
sentimentURL = 'http://text-processing.com/api/sentiment/'

# tweet id list
tweet_ids = []

# file to hold twitter user ids
twitter_users_file = './twitteruserids.txt'

prev_time = time.time()
sentiment_avg = [0.0,0.0,0.0]


class TweetStreamListener(StreamListener):

    def __init__(self):
        self.count = 0
        self.count_filtered = 0
        self.filter_ratio = 0

    # on success
    def on_data(self, data):
        try:
            self.count+=1
            # decode json
            dict_data = json.loads(data)

            print("\n------------------------------> (tweets: %s, filtered: %s, filter-ratio: %s)" \
                % (self.count, self.count_filtered, str(round(self.count_filtered/self.count*100,2))+"%"))
            logger.debug('tweet data: ' + str(dict_data))

            text = dict_data["text"]
            if text is None:
                logger.info("Tweet has no relevant text, skipping")
                self.count_filtered+=1
                return True

            # grab html links from tweet
            tweet_urls = []
            if args.linksentiment:
                tweet_urls = re.findall(r'(https?://[^\s]+)', text)

            # clean up tweet text
            textclean = clean_text(text)

            # check if tweet has no valid text
            if textclean == "":
                logger.info("Tweet does not cotain any valid text after cleaning, not adding")
                self.count_filtered+=1
                return True

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
            text_filtered = str(textclean)
            tweetid = int(dict_data.get("id"))
            text_raw = str(dict_data.get("text"))

            # output twitter data
            print("\n<------------------------------")
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
            # convert to lower case
            tokens = [w.lower() for w in tokens]
            # remove punctuation from each word
            table = str.maketrans('', '', string.punctuation)
            stripped = [w.translate(table) for w in tokens]
            # remove remaining tokens that are not alphabetic
            tokens = [w for w in stripped if w.isalpha()]
            # filter out stop words
            stop_words = set(nltk.corpus.stopwords.words('english'))
            tokens = [w for w in tokens if not w in stop_words]
            # remove words less than 3 characters
            tokens = [w for w in tokens if not len(w) < 3]
            print("NLTK Tokens: " + str(tokens))

            # check for min token length
            if len(tokens) < 5:
                logger.info("Tweet does not contain min. number of tokens, not adding")
                self.count_filtered+=1
                return True

            # do some checks before adding to elasticsearch and crawling urls in tweet
            if friends == 0 or \
                            followers == 0 or \
                            statuses == 0 or \
                            text == "" or \
                            tweetid in tweet_ids:
                logger.info("Tweet doesn't meet min requirements, not adding")
                self.count_filtered+=1
                return True

            # check ignored tokens from config
            for t in nltk_tokens_ignored:
                if t in tokens:
                    logger.info("Tweet contains token from ignore list, not adding")
                    self.count_filtered+=1
                    return True
            # check required tokens from config
            tokenspass = False
            tokensfound = 0
            for t in nltk_tokens_required:
                if t in tokens:
                    tokensfound += 1
                    if tokensfound == nltk_min_tokens:
                        tokenspass = True
                        break
            if not tokenspass:
                logger.info("Tweet does not contain token from required list or min required, not adding")
                self.count_filtered+=1
                return True

            # clean text for sentiment analysis
            text_clean = clean_text_sentiment(text_filtered)

            # check if tweet has no valid text
            if text_clean == "":
                logger.info("Tweet does not cotain any valid text after cleaning, not adding")
                self.count_filtered+=1
                return True

            print("Tweet Clean Text (sentiment): " + text_clean)

            # get sentiment values
            polarity, subjectivity, sentiment = sentiment_analysis(text_clean)

            # add tweet_id to list
            tweet_ids.append(dict_data["id"])

            # get sentiment for tweet 
            if len(tweet_urls) > 0:
                tweet_urls_polarity = 0
                tweet_urls_subjectivity = 0
                for url in tweet_urls:
                    res = tweeklink_sentiment_analysis(url)
                    if res is None:
                        continue
                    pol, sub, sen = res
                    tweet_urls_polarity = (tweet_urls_polarity + pol) / 2
                    tweet_urls_subjectivity = (tweet_urls_subjectivity + sub) / 2
                    if sentiment == "positive" or sen == "positive":
                        sentiment = "positive"
                    elif sentiment == "negative" or sen == "negative":
                        sentiment = "negative"
                    else:
                        sentiment = "neutral"

                # calculate average polarity and subjectivity from tweet and tweet links
                if tweet_urls_polarity > 0:
                    polarity = (polarity + tweet_urls_polarity) / 2
                if tweet_urls_subjectivity > 0:
                    subjectivity = (subjectivity + tweet_urls_subjectivity) / 2
            

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

            # randomly sleep to stagger request time
            time.sleep(randrange(2,5))
            return True

        except Exception as e:
            logger.warning("Exception: exception caused by: %s" % e)
            raise

    # on failure
    def on_error(self, status_code):
        logger.error("Got an error with status code: %s (will try again later)" % status_code)
        # randomly sleep to stagger request time
        time.sleep(randrange(2,30))
        return True

    # on timeout
    def on_timeout(self):
        logger.warning("Timeout... (will try again later)")
        # randomly sleep to stagger request time
        time.sleep(randrange(2,30))
        return True


class NewsHeadlineListener:

    def __init__(self, url=None, frequency=120):
        self.url = url
        self.headlines = []
        self.followedlinks = []
        self.frequency = frequency
        self.count = 0
        self.count_filtered = 0
        self.filter_ratio = 0

        while True:
            new_headlines = self.get_news_headlines(self.url)

            # add any new headlines
            for htext, htext_url in new_headlines:
                if htext not in self.headlines:
                    self.headlines.append(htext)
                    self.count+=1

                    datenow = datetime.utcnow().isoformat()
                    # output news data
                    print("\n------------------------------> (news headlines: %s, filtered: %s, filter-ratio: %s)" \
                        % (self.count, self.count_filtered, str(round(self.count_filtered/self.count*100,2))+"%"))
                    print("Date: " + datenow)
                    print("News Headline: " + htext)
                    print("Location (url): " + htext_url)

                    # create tokens of words in text using nltk
                    text_for_tokens = re.sub(
                        r"[\%|\$|\.|\,|\!|\:|\@]|\(|\)|\#|\+|(``)|('')|\?|\-", "", htext)
                    tokens = nltk.word_tokenize(text_for_tokens)
                    print("NLTK Tokens: " + str(tokens))

                    # check for min token length
                    if len(tokens) < 5:
                        logger.info("Text does not contain min. number of tokens, not adding")
                        self.count_filtered+=1
                        continue

                    # check ignored tokens from config
                    for t in nltk_tokens_ignored:
                        if t in tokens:
                            logger.info("Text contains token from ignore list, not adding")
                            self.count_filtered+=1
                            continue
                    # check required tokens from config
                    tokenspass = False
                    for t in nltk_tokens_required:
                        if t in tokens:
                            tokenspass = True
                            break
                    if not tokenspass:
                        logger.info("Text does not contain token from required list, not adding")
                        self.count_filtered+=1
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


def clean_text(text):
    # clean up text
    text = text.replace("\n", " ")
    text = re.sub(r"https?\S+", "", text)
    text = re.sub(r"&.*?;", "", text)
    text = re.sub(r"<.*?>", "", text)
    text = text.replace("RT", "")
    text = text.replace(u"…", "")
    text = text.strip()
    return text


def clean_text_sentiment(text):
    # clean up text for sentiment analysis
    text = re.sub(r"[#|@]\S+", "", text)
    text = text.strip()
    return text


def get_sentiment_from_url(text, sentimentURL):
    # get sentiment from text processing website
    payload = {'text': text}

    try:
        #logger.debug(text)
        post = requests.post(sentimentURL, data=payload)
        #logger.debug(post.status_code)
        #logger.debug(post.text)
    except requests.exceptions.RequestException as re:
        logger.error("Exception: requests exception getting sentiment from url caused by %s" % re)
        raise

    # return None if we are getting throttled or other connection problem
    if post.status_code != 200:
        logger.warning("Can't get sentiment from url caused by %s %s" % (post.status_code, post.text))
        return None

    response = post.json()

    neg = response['probability']['neg']
    pos = response['probability']['pos']
    neu = response['probability']['neutral']
    label = response['label']

    # determine if sentiment is positive, negative, or neutral
    if label == "neg":
        sentiment = "negative"
    elif label == "neutral":
        sentiment = "neutral"
    else:
        sentiment = "positive"

    return sentiment, neg, pos, neu


def sentiment_analysis(text):
    """Determine if sentiment is positive, negative, or neutral
    algorithm to figure out if sentiment is positive, negative or neutral
    uses sentiment polarity from TextBlob, VADER Sentiment and
    sentiment from text-processing URL
    could be made better :)
    """

    # pass text into sentiment url
    if args.websentiment:
        ret = get_sentiment_from_url(text, sentimentURL)
        if ret is None:
            sentiment_url = None
        else:
            sentiment_url, neg_url, pos_url, neu_url = ret
    else:
        sentiment_url = None

    # pass text into TextBlob
    text_tb = TextBlob(text)

    # pass text into VADER Sentiment
    analyzer = SentimentIntensityAnalyzer()
    text_vs = analyzer.polarity_scores(text)

    # determine sentiment from our sources
    if sentiment_url is None:
        if text_tb.sentiment.polarity < 0 and text_vs['compound'] <= -0.05:
            sentiment = "negative"
        elif text_tb.sentiment.polarity > 0 and text_vs['compound'] >= 0.05:
            sentiment = "positive"
        else:
            sentiment = "neutral"
    else:
        if text_tb.sentiment.polarity < 0 and text_vs['compound'] <= -0.05 and sentiment_url == "negative":
            sentiment = "negative"
        elif text_tb.sentiment.polarity > 0 and text_vs['compound'] >= 0.05 and sentiment_url == "positive":
            sentiment = "positive"
        else:
            sentiment = "neutral"

    # calculate average polarity from TextBlob and VADER
    polarity = (text_tb.sentiment.polarity + text_vs['compound']) / 2

    # output sentiment polarity
    print("************")
    print("Sentiment Polarity: " + str(round(polarity, 3)))

    # output sentiment subjectivity (TextBlob)
    print("Sentiment Subjectivity: " + str(round(text_tb.sentiment.subjectivity, 3)))

    # output sentiment
    print("Sentiment (url): " + str(sentiment_url))
    print("Sentiment (algorithm): " + str(sentiment))
    print("Overall sentiment (textblob): ", text_tb.sentiment) 
    print("Overall sentiment (vader): ", text_vs) 
    print("sentence was rated as ", round(text_vs['neg']*100, 3), "% Negative") 
    print("sentence was rated as ", round(text_vs['neu']*100, 3), "% Neutral") 
    print("sentence was rated as ", round(text_vs['pos']*100, 3), "% Positive") 
    print("************")

    return polarity, text_tb.sentiment.subjectivity, sentiment


def tweeklink_sentiment_analysis(url):
    # get text summary of tweek link web page and run sentiment analysis on it
    try:
        logger.info('Following tweet link %s to get sentiment..' % url)
        article = Article(url)
        article.download()
        article.parse()
        # check if twitter web page
        if "Tweet with a location" in article.text:
            logger.info('Link to Twitter web page, skipping')
            return None
        article.nlp()
        tokens = article.keywords
        print("Tweet link nltk tokens:", tokens)

        # check for min token length
        if len(tokens) < 5:
            logger.info("Tweet link does not contain min. number of tokens, not adding")
            return None
        # check ignored tokens from config
        for t in nltk_tokens_ignored:
            if t in tokens:
                logger.info("Tweet link contains token from ignore list, not adding")
                return None
        # check required tokens from config
        tokenspass = False
        tokensfound = 0
        for t in nltk_tokens_required:
            if t in tokens:
                tokensfound += 1
                if tokensfound == nltk_min_tokens:
                    tokenspass = True
                    break
        if not tokenspass:
            logger.info("Tweet link does not contain token from required list or min required, not adding")
            return None

        summary = article.summary
        if summary == '':
            logger.info('No text found in tweet link url web page')
            return None
        summary_clean = clean_text(summary)
        summary_clean = clean_text_sentiment(summary_clean)
        print("Tweet link Clean Summary (sentiment): " + summary_clean)
        polarity, subjectivity, sentiment = sentiment_analysis(summary_clean)
        
        return polarity, subjectivity, sentiment

    except ArticleException as e:
        logger.warning('Exception: error getting text on Twitter link caused by: %s' % e)
        return None


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
    parser.add_argument("-s", "--symbol", metavar="SYMBOL", required=True,
                        help="Stock symbol you are interesed in searching for, example: TSLA")
    parser.add_argument("-k", "--keywords", metavar="KEYWORDS",
                        help="Use keywords to search for in Tweets instead of feeds. "
                             "Separated by comma, case insensitive, spaces are ANDs commas are ORs. "
                             "Example: TSLA,'Elon Musk',Musk,Tesla,SpaceX")
    parser.add_argument("-a", "--addtokens", action="store_true",
                        help="Add nltk tokens required from config to keywords")
    parser.add_argument("-u", "--url", metavar="URL",
                        help="Use twitter users from any links in web page at url")
    parser.add_argument("-f", "--file", metavar="FILE",
                        help="Use twitter user ids from file")
    parser.add_argument("-l", "--linksentiment", action="store_true",
                        help="Follow any link url in tweets and analyze sentiment on web page")
    parser.add_argument("-n", "--newsheadlines", action="store_true",
                        help="Get news headlines instead of Twitter using stock symbol from -s")
    parser.add_argument("--frequency", metavar="FREQUENCY", default=120, type=int,
                        help="How often in seconds to retrieve news headlines (default: 120 sec)")
    parser.add_argument("--followlinks", action="store_true",
                        help="Follow links on news headlines and scrape relevant text from landing page") 
    parser.add_argument("-w", "--websentiment", action="store_true",
                        help="Get sentiment results from text processing website")                  
    parser.add_argument("--overridetokensreq", metavar="TOKEN", nargs="+",
                        help="Override nltk required tokens from config, separate with space")
    parser.add_argument("--overridetokensignore", metavar="TOKEN", nargs="+",
                        help="Override nltk ignore tokens from config, separate with space")
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
       _                     _                 
     _| |_ _           _   _| |_ _     _   _   
    |   __| |_ ___ ___| |_|   __|_|___| |_| |_ 
    |__   |  _| . |  _| '_|__   | | . |   |  _|
    |_   _|_| |___|___|_,_|_   _|_|_  |_|_|_|  
      |_|                   |_|   |___|                
          :) = +$   :( = -$    v%s
     https://github.com/shirosaidev/stocksight
            \033[0m""" % (color, STOCKSIGHT_VERSION)
        print(banner + '\n')

    # create instance of elasticsearch
    es = Elasticsearch(hosts=[{'host': elasticsearch_host, 'port': elasticsearch_port}],
                http_auth=(elasticsearch_user, elasticsearch_password))

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

    # check if we need to override any tokens
    if args.overridetokensreq:
        nltk_tokens_required = tuple(args.overridetokensreq)
    if args.overridetokensignore:
        nltk_tokens_ignored = tuple(args.overridetokensignore)

    # are we grabbing news headlines from yahoo finance or twitter
    if args.newsheadlines:
        try:
            url = "https://finance.yahoo.com/quote/%s/?p=%s" % (args.symbol, args.symbol)

            logger.info('NLTK tokens required: ' + str(nltk_tokens_required))
            logger.info('NLTK tokens ignored: ' + str(nltk_tokens_ignored))
            logger.info("Scraping news for %s from %s ..." % (args.symbol, url))

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
        elif args.keywords is None:
            # build user id list from user names
            logger.info("Looking up Twitter user ids from usernames... (use -f twitteruserids.txt for cached user ids)")
            useridlist = []
            while True:
                for u in twitter_feeds:
                    try:
                        # get user id from screen name using twitter api
                        user = api.get_user(screen_name=u)
                        uid = str(user.id)
                        if uid not in useridlist:
                            useridlist.append(uid)
                        time.sleep(randrange(2, 5))
                    except TweepError as te:
                        # sleep a bit in case twitter suspends us
                        logger.warning("Tweepy exception: twitter api error caused by: %s" % te)
                        logger.info("Sleeping for a random amount of time and retrying...")
                        time.sleep(randrange(2,30))
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
            logger.info('Stock symbol: ' + str(args.symbol))
            logger.info('NLTK tokens required: ' + str(nltk_tokens_required))
            logger.info('NLTK tokens ignored: ' + str(nltk_tokens_ignored))
            logger.info('Listening for Tweets (ctrl-c to exit)...')
            if args.keywords is None:
                logger.info('No keywords entered, following Twitter users...')
                logger.info('Twitter Feeds: ' + str(twitter_feeds))
                logger.info('Twitter User Ids: ' + str(useridlist))
                stream.filter(follow=useridlist, languages=['en'])
            else:
                # keywords to search on twitter
                # add keywords to list
                keywords = args.keywords.split(',')
                if args.addtokens:
                    # add tokens to keywords to list
                    for f in nltk_tokens_required:
                        keywords.append(f)
                logger.info('Searching Twitter for keywords...')
                logger.info('Twitter keywords: ' + str(keywords))
                stream.filter(track=keywords, languages=['en'])
        except TweepError as te:
            logger.debug("Tweepy Exception: Failed to get tweets caused by: %s" % te)
        except KeyboardInterrupt:
            print("Ctrl-c keyboard interrupt, exiting...")
            stream.disconnect()
            sys.exit(0)
