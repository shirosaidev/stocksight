class Article:

    def __init__(self, title, url, body='', referer_url=''):
        self.title = title
        self.body = body
        self.url = url
        self.referer_url = referer_url

    def __eq__(self, other):
        return self.url == other.url and self.title == other.title
