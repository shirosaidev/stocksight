#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""SeekAlphaListener.py - get headline sentiment from SeekingAlpha and add to
Elasticsearch.
See README.md or https://github.com/shirosaidev/stocksight
for more information.

Copyright (C) Chris Park 2018-2019
Copyright (C) Allen (Jian Feng) Xie 2019
stocksight is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""
from StockSight.NewsHeadlineListener import *


class YahooFinanceListener(NewsHeadlineListener):
    def __init__(self, symbol):
        super(YahooFinanceListener, self)\
            .__init__("Yahoo Finance", symbol, "https://finance.yahoo.com/quote/%s/?p=%s" % (symbol, symbol))

    def get_news_headlines(self):

        articles = []

        parsed_uri = urlparse.urljoin(self.url, '/')

        try:
            soup = self.get_soup(self.url)
            html = soup.findAll('h3')

            if html:
                for rawArticle in html:

                    article = self.get_article_with_atag(rawArticle, parsed_uri)
                    if self.can_process(article):
                        if config['news']['follow_link']:
                            body_url = article.url
                            for p in self.get_page_text(body_url, 'p'):
                                article.body += str(p)+" "

                        article.referer_url = self.url
                        articles.append(article)

        except requests.exceptions.RequestException as exce:
            logger.warning("Exception: can't crawl web site (%s)" % exce)
            pass

        return articles

    def get_page_text(self, url, selector):
        max_paragraphs = 10
        try:
            soup = self.get_soup(url)
            html_p = soup.findAll(selector)

            if html_p:
                n = 1
                for i in html_p:
                    if n <= max_paragraphs:
                        if i.text is not None:
                            yield i.text
                    else:
                        break
                    n += 1

        except requests.exceptions.RequestException as re:
            logger.warning("Exception: can't crawl web site (%s)" % re)
            pass
