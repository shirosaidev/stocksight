import hashlib
import re
from datetime import datetime

import nltk

try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse

from config import *
from Sentiment.Initializer.ElasticSearchInit import es
from Sentiment.Initializer.str_unicode import *
from Sentiment.Initializer.RedisInit import rds
from Sentiment.Helper.Sentiment import *


class NewsHeadlineListener:
    def __init__(self, symbol,url=None):
        self.symbol = symbol
        self.url = url

        new_headlines = self.get_news_headlines(self.url)

        # add any new headlines
        for htext, htext_url in new_headlines:

            md5_hash = hashlib.md5((htext+htext_url).encode()).hexdigest()

            if rds.exists(md5_hash) is 0:

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
                        rds.set(md5_hash,1,2628000)
                        continue
                # check required tokens from config
                tokenspass = False


                if self.symbol in nltk_tokens_required:
                    nltk_tokens = nltk_tokens_required[self.symbol]
                else:
                    nltk_tokens = nltk_tokens_required['default']

                for t in nltk_tokens:
                    if t in tokens:
                        tokenspass = True
                        break
                if not tokenspass:
                    logger.info("Text does not contain token from required list, not adding")
                    rds.set(md5_hash,1,2628000)
                    continue

                # get sentiment values
                polarity, subjectivity, sentiment = sentiment_analysis(htext)

                logger.info("Adding news headline to elasticsearch")
                # add news headline data and sentiment info to elasticsearch
                es.index(index=self.symbol,
                         doc_type="newsheadline",
                         body={"date": datenow,
                               "location": htext_url,
                               "message": htext,
                               "polarity": polarity,
                               "subjectivity": subjectivity,
                               "sentiment": sentiment})
                rds.set(md5_hash,1,2628000)


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
                    latestheadlines.append((unicode(i.next.next.next.next), url))
            logger.debug(latestheadlines)

            if follow_link:
                if links:
                    for i in links:
                        if '/news/' in i['href']:
                            l = parsed_uri.rstrip('/') + i['href']
                            latestheadlines_links.append(l)

                logger.debug(latestheadlines_links)

                logger.info("Following any new links and grabbing text from page...")

                for linkurl in latestheadlines_links:
                    for p in get_page_text(linkurl):
                        latestheadlines.append((unicode(p), linkurl))
                logger.debug(latestheadlines)

        except requests.exceptions.RequestException as re:
            logger.warning("Exception: can't crawl web site (%s)" % re)
            pass

        return latestheadlines

