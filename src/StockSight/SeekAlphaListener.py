from StockSight.NewsHeadlineListener import *


class SeekAlphaListener(NewsHeadlineListener):
    def __init__(self, symbol):
        super(SeekAlphaListener, self)\
            .__init__("Seek Alpha", symbol, "https://seekingalpha.com/symbol/%s" % symbol)

    def get_news_headlines(self):

        articles = []

        parsed_uri = urlparse.urljoin(self.url, '/')

        try:
            req = requests.get(self.url)
            html = req.text
            soup = BeautifulSoup(html, 'html.parser')
            analysis = soup.select('div.analysis div.symbol_article')
            news = soup.select('div.news div.symbol_article')

            if analysis:
                for rawArticle in analysis:
                    article = self.get_article_with_atag(rawArticle, parsed_uri)
                    if self.can_process(article):
                        if config['news']['follow_link']:
                            body_url = article.url
                            for p in self.get_analysis_summary(body_url):
                                article.body += str(p)+" "

                        article.referer_url = self.url
                        articles.append(article)

            if news:
                for rawArticle in news:
                    article = self.get_article_with_atag(rawArticle, parsed_uri)
                    if self.can_process(article):
                        if config['news']['follow_link']:
                            body_url = article.url
                            for p in self.get_news_summary(body_url):
                                article.body += str(p)+" "

                        article.referer_url = self.url
                        articles.append(article)

        except requests.exceptions.RequestException as exce:
            logger.warning("Exception: can't crawl web site (%s)" % exce)
            pass

        return articles

    def get_page_text(self, url):
        pass

    def get_news_summary(self, url):
        try:
            req = requests.get(url)
            html = req.text
            soup = BeautifulSoup(html, 'html.parser')
            html_p = soup.select('p.bullets_li')

            if html_p:
                for i in html_p:
                    if i.string is not None:
                        yield i.string
                    else:
                        break

        except requests.exceptions.RequestException as exce:
            logger.warning("Exception: can't crawl web site (%s)" % exce)
            pass

    def get_analysis_summary(self, url):
        try:
            req = requests.get(str(url))
            html = req.text
            soup = BeautifulSoup(html, 'html.parser')
            html_p = soup.select('div.a-sum p')

            if html_p:
                for i in html_p:
                    if i.string is not None:
                        yield i.string
                    else:
                        break

        except requests.exceptions.RequestException as exce:
            logger.warning("Exception: can't crawl web site (%s)" % exce)
            pass
