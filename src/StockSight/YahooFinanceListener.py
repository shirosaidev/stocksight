from StockSight.NewsHeadlineListener import *


class YahooFinanceListener(NewsHeadlineListener):
    def __init__(self,symbol):
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

                    aTag = rawArticle.find('a')
                    article = Article(aTag.text, aTag.get('href'))

                    if config['news']['follow_link']:
                        new_url = parsed_uri + article.url
                        for p in self.get_page_text(new_url):
                            article.body += str(p)

                    article.refer_url = self.url
                    articles.append(article)

        except requests.exceptions.RequestException as re:
            logger.warning("Exception: can't crawl web site (%s)" % re)
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
