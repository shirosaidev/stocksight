#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""stockprice.py - get stock price from Yahoo and add to
Elasticsearch.
See README.md or https://github.com/shirosaidev/stocksight
for more information.

Copyright (C) Chris Park 2018
Copyright (C) Allen (Jian Feng) Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

import argparse
import sys
from random import randint

from StockSight.TweetListener import *


STOCKSIGHT_VERSION = '0.1-b.6'
__version__ = STOCKSIGHT_VERSION


if __name__ == '__main__':
    # parse cli args
    parser = argparse.ArgumentParser()
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

    if args.verbose:
        logger.setLevel(logging.INFO)
        eslogger.setLevel(logging.INFO)
        requestslogger.setLevel(logging.INFO)
    if args.debug:
        logger.setLevel(logging.DEBUG)
        eslogger.setLevel(logging.DEBUG)
        requestslogger.setLevel(logging.DEBUG)
    if args.quiet:
        logger.disabled = True
        eslogger.disabled = True
        requestslogger.disabled = True


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

    #TODO exit if the twitter keys are empty
    if not consumer_key or \
       not consumer_secret or \
       not access_token or \
       not access_token_secret:
        logger.warning("Invalid Twitter API cred")
        sys.exit(1)


    try:
        for symbol in symbols:
            try:
                logger.info('Creating new Elasticsearch index or using existing ' + symbol)
                es.indices.create(index=symbol, body=mappings, ignore=[400, 404])

                logger.info('NLTK tokens required: ' + str(nltk_tokens_required))
                logger.info('NLTK tokens ignored: ' + str(nltk_tokens_ignored))
                logger.info("Scraping tweets for %s from %s ..." % (symbol))

                # create instance of TweetStreamListener
                TweetStreamListener = TweetStreamListener(symbol)

                # set twitter keys/tokens
                auth = OAuthHandler(consumer_key, consumer_secret)
                auth.set_access_token(access_token, access_token_secret)
                api = API(auth)

                # create instance of the tweepy stream
                stream = Stream(auth, TweetStreamListener)

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
                    logger.info('Writing twitter user ids to text file %s' % TweetStreamListener.twitter_users_file)
                    try:
                        f = open(TweetStreamListener.twitter_users_file, "wt", encoding='utf-8')
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

            except Exception as e:
                logger.warning("%s" % e)
                pass

    except KeyboardInterrupt:
        print("Ctrl-c keyboard interrupt, exiting...")
        sys.exit(0)