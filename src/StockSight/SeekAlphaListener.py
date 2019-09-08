from StockSight.NewsHeadlineListener import *


class SeekAlphaListener(NewsHeadlineListener):
    def __init__(self,symbol):
        super.__init__(symbol,"https://finance.yahoo.com/quote/%s/?p=%s" % (symbol, symbol))

    def get_news_headlines(self):

        latestheadlines = []
        latestheadlines_links = []

        parsed_uri = urlparse.urljoin(self.url, '/')

        try:

            req = requests.get(self.url)
            html = req.text
            soup = BeautifulSoup(html, 'html.parser')
            html = soup.findAll('h3')
            links = soup.findAll('a')

            if html:
                for i in html:
                    latestheadlines.append((str(i.next.next.next.next), self.url))
            logger.debug(latestheadlines)

            if config['news']['follow_link']:
                if links:
                    for i in links:
                        if '/news/' in i['href']:
                            l = parsed_uri.rstrip('/') + i['href']
                            latestheadlines_links.append(l)

                logger.debug(latestheadlines_links)

                logger.info("Following any new links and grabbing text from page...")

                for linkurl in latestheadlines_links:
                    for p in self.get_page_text(linkurl):
                        latestheadlines.append((str(p), linkurl))
                logger.debug(latestheadlines)

        except requests.exceptions.RequestException as re:
            logger.warning("Exception: can't crawl web site (%s)" % re)
            pass

        return latestheadlines

        def get_page_text(self):
            pass