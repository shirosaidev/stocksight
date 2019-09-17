#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""stockprice.py - get stock price from Yahoo and add to
Elasticsearch.
See README.md or https://github.com/shirosaidev/stocksight
for more information.

Copyright (C) Chris Park 2018-2019
Copyright (C) Allen (Jian Feng) Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

import json
import re
import time

import nltk

from StockSight.Initializer.ConfigReader import *
from StockSight.Initializer.ElasticSearch import es
from StockSight.Initializer.Redis import rds
from StockSight.Helper.Sentiment import *

from tweepy.streaming import StreamListener


class TweetStreamListener(StreamListener):

    # file to hold twitter user ids
    twitter_users_file = './twitteruserids.txt'

    # on success
    def on_data(self, data):

        try:
            # decode json
            dict_data = json.loads(data)

            logger.debug(dict_data)

            # clean up tweet text
            # text = unicodedata.normalize(
            #    'NFKD', dict_data["text"]).encode('ascii', 'ignore')
            text = dict_data["text"]
            if text is None:
                logger.info("Tweet has no relevant text, skipping")
                return True

            # grab html links from tweet
            # tweet_urls = re.search("http\S+", text)

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
            text_raw = str(dict_data.get("text"))

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
               followers < config['twitter']['min_followers'] or \
               statuses == 0 or \
               text == "":
                logger.info("Tweet doesn't meet min requirements, not adding")
                return True

            redis_id = 'tweet'+str(tweetid)
            if rds.exists(redis_id):
                logger.info("Tweet already exists")
                return True

            # check ignored tokens from config
            for t in config['sentiment_analyzer']['ignore_words']:
                if t in tokens:
                    logger.info("Tweet contains token from ignore list, not adding")
                    return True
            # check required tokens from config
            tokenspass = False
            for key in config['symbols']:
                self.symbol = key
                for t in config['symbols'][key]:
                    if t in tokens:
                        tokenspass = True
                        break
                if tokenspass:
                    break

            if not tokenspass:
                logger.info("Tweet does not contain token from required list, not adding")
                return True

            # strip out hashtags for language processing
            tweet = re.sub(r"[#|@|\$]\S+", "", text)
            tweet.strip()

            # get sentiment values
            polarity, subjectivity, sentiment = sentiment_analysis(tweet)

            # remove hashtags for elasticsearch
            # text_filtered = re.sub(r"[#|@|\$]\S+", "", text_filtered)

            self.index_name = config['elasticsearch']['table_prefix']['sentiment']+self.symbol.lower()
            logger.info("Adding tweet to elasticsearch")
            # add twitter data and sentiment info to elasticsearch
            es.index(index=self.index_name,
                     doc_type="_doc",
                     body={
                           "_id": redis_id,
                           "author": screen_name,
                           "location": location,
                           "date": created_date,
                           "title": text_filtered,
                           "message": '',
                           "polarity": polarity,
                           "subjectivity": subjectivity,
                           "sentiment": sentiment
                     })

            # add tweet_id to cache
            rds.set(redis_id, 1, 86400)

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
    except requests.exceptions.RequestException as exce:
        logger.warning("Requests exception: can't crawl web site caused by: %s" % exce)
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
        f.close()
    except (IOError, OSError) as e:
        logger.warning("Exception: error opening file caused by: %s" % e)
        pass

    return twitter_users
