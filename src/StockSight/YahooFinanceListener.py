from StockSight.NewsHeadlineListener import *


class YahooFinanceListener(NewsHeadlineListener):
    def __init__(self, symbol):
        super(YahooFinanceListener, self)\
            .__init__("Yahoo Finance", symbol, "https://finance.yahoo.com/quote/%s/?p=%s" % (symbol, symbol))

    def get_news_headlines(self):

        articles = []

        parsed_uri = urlparse.urljoin(self.url, '/')

        try:

            req = requests.get(self.url)
            html = req.text
            soup = BeautifulSoup(html, 'html.parser')
            html = soup.findAll('h3')

            if html:
                for rawArticle in html:

                    article = self.get_article_with_atag(rawArticle, parsed_uri)
                    if self.can_process(article):
                        if config['news']['follow_link']:
                            body_url = self.get_proper_new_body_url(article.url, parsed_uri)
                            for p in self.get_page_text(body_url):
                                article.body += str(p)+" "

                        article.referer_url = self.url
                        articles.append(article)

        except requests.exceptions.RequestException as exce:
            logger.warning("Exception: can't crawl web site (%s)" % exce)
            pass

        return articles

    def get_page_text(self, url):
        max_paragraphs = 5
        try:
            req = requests.get(url)
            html = req.text
            soup = BeautifulSoup(html, 'html.parser')
            html_p = soup.findAll('p')

            if html_p:
                n = 1
                for i in html_p:
                    if n <= max_paragraphs:
                        if i.string is not None:
                            yield i.string
                    else:
                        break
                    n += 1

        except requests.exceptions.RequestException as re:
            logger.warning("Exception: can't crawl web site (%s)" % re)
            pass
