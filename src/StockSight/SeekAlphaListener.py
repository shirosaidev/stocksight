#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""SeekAlphaListener.py - get headline sentiment from SeekingAlpha and add to
Elasticsearch.
See README.md or https://github.com/shirosaidev/stocksight
for more information.

Copyright (C) Allen (Jian Feng) Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

from StockSight.NewsHeadlineListener import *
import time
from random import randint

class SeekAlphaListener(NewsHeadlineListener):
    def __init__(self, symbol):
        super(SeekAlphaListener, self)\
            .__init__("Seek Alpha", symbol, "https://seekingalpha.com/symbol/%s" % symbol)

    def get_news_headlines(self):

        articles = []

        parsed_uri = urlparse.urljoin(self.url, '/')

        try:
            soup = self.get_soup(self.url)
            analysis = soup.select('div.analysis div.symbol_article')
            news = soup.select('div.news div.symbol_article')

            if analysis:

                for rawArticle in analysis:
                    article = self.get_article_with_atag(rawArticle, parsed_uri)
                    if self.can_process(article):

                        # if config['news']['follow_link']:
                        #     body_url = article.url
                        #     for p in self.get_analysis_summary(body_url, 'p.bullets_li'):
                        #         article.body += str(p)+" "

                        article.referer_url = self.url
                        articles.append(article)

            if news:
                for rawArticle in news:
                    article = self.get_article_with_atag(rawArticle, parsed_uri)
                    if self.can_process(article):

                        # if config['news']['follow_link']:
                        #     body_url = article.url
                        #     for p in self.get_summary(body_url, 'div.a-sum p'):
                        #         article.body += str(p)+" "

                        article.referer_url = self.url
                        articles.append(article)

        except requests.exceptions.RequestException as exce:
            logger.warning("Exception: can't crawl web site (%s)" % exce)
            pass

        return articles

    def get_page_text(self, url):
        pass

    def get_summary(self, url, selector):
        try:
            soup = self.get_soup(url)
            html_p = soup.select(selector)

            if html_p:
                for i in html_p:
                    if i.text is not None:
                        yield i.text
                    else:
                        break

        except requests.exceptions.RequestException as exce:
            logger.warning("Exception: can't crawl web site (%s)" % exce)
            pass
