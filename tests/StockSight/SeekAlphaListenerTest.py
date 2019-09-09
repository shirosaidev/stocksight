import unittest
from StockSight.SeekAlphaListener import *
from StockSight.EsMap.Sentiment import mapping


class SeekAlphaListenerTest(unittest.TestCase):

    symbol = 'tsla'

    def setUp(self):
        config['redis']['db'] = 1
        self.mainClass = SeekAlphaListener(self.symbol)

    @classmethod
    def setUpClass(cls):
        cls.index_name = "stocksight_sentiment_test_"+cls.symbol
        es.indices.create(index=cls.index_name, body=mapping, ignore=[400, 404])

    @classmethod
    def tearDownClass(cls):
        rds.flushdb()
        es.indices.delete(index=cls.index_name, ignore=[400, 404])

    def test_get_news_headlines(self):
        headlines = self.mainClass.get_news_headlines()
        self.assertGreaterEqual(headlines.__len__(), 1, "Empty Headline")
        self.assertIsInstance(headlines[0], Article, "Is not an Article")
        self.assertIsNotNone(headlines[0].title, "Title is empty")
        self.assertIsNotNone(headlines[0].url, "URL is empty")
        self.assertIsNotNone(headlines[0].referer_url, "Refer URL is empty")

    def test_get_news_headlines_with_body(self):
        config['news']['follow_link'] = True
        headlines = self.mainClass.get_news_headlines()
        self.assertGreaterEqual(headlines.__len__(), 1, "Empty Headline")
        self.assertIsInstance(headlines[0], Article, "Is not an Article")
        self.assertIsNotNone(headlines[0].title, "Title is empty")
        self.assertIsNotNone(headlines[0].url, "URL is empty")
        self.assertNotEqual(headlines[0].referer_url, '', "Refer URL is empty")
        for message in headlines:
            if message.body == '': continue;
            else:
                self.assertNotEqual(headlines[0].body, '', "Body is empty")
                break

    def test_execute(self):
        self.mainClass.index_name = self.index_name
        self.mainClass.execute()
        logs = es.search(index=self.index_name,body="{}")
        message = logs['hits']['hits'][0]['_source']
        self.assertIsNotNone(message['title'], "Title is empty")
        self.assertIsNotNone(message['url'], "URL is empty")
        self.assertNotEqual(message['referer_url'], '', "Refer URL is empty")
        self.assertIsNotNone(message['sentiment'], "Sentiment is empty")
        self.assertIsNotNone(message['polarity'], "Polarity is empty")

if __name__ == '__main__':
    unittest.main()