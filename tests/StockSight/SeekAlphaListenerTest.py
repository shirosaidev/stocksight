import unittest
from StockSight.SeekAlphaListener import *
from StockSight.EsMap.Sentiment import mapping
import time


class SeekAlphaListenerTest(unittest.TestCase):

    symbol = 'tsla'

    def setUp(self):
        config['redis']['db'] = 1
        self.mainClass = SeekAlphaListener(self.symbol)

    def tearDown(self):
        rds.flushdb()

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
        self.assertGreaterEqual(headlines.__len__(), 1, "Empty Headline / Page returned 403")
        self.assertIsInstance(headlines[0], Article, "Is not an Article")
        self.assertIsNotNone(headlines[0].title, "Title is empty")
        self.assertIsNotNone(headlines[0].url, "URL is empty")
        self.assertIsNotNone(headlines[0].referer_url, "Refer URL is empty")

    def test_get_news_headlines_with_body(self):
        config['news']['follow_link'] = True
        headlines = self.mainClass.get_news_headlines()
        self.assertGreaterEqual(headlines.__len__(), 1, "Empty Headline / Page returned 403")
        self.assertIsInstance(headlines[0], Article, "Is not an Article")
        self.assertIsNotNone(headlines[0].title, "Title is empty")
        self.assertIsNotNone(headlines[0].url, "URL is empty")
        self.assertNotEqual(headlines[0].referer_url, '', "Refer URL is empty")
        has_article_body = False
        has_news_body = False
        for message in headlines:
            if message.body == '':
                continue
            elif message.url.find('article') > -1:
                has_article_body = True
            elif message.url.find('news') > -1:
                has_news_body = True

            if has_article_body and has_news_body:
                break;

        self.assertEqual(has_news_body, True, "News body is empty")
        self.assertEqual(has_article_body, True, "Article body is empty")


    def test_execute(self):
        self.mainClass.index_name = self.index_name
        self.mainClass.execute()
        time.sleep(1)
        logs = es.search(index=self.index_name,body="{}")
        message = logs['hits']['hits'][0]['_source']
        self.assertIsNotNone(message['title'], "Title is empty")
        self.assertIsNotNone(message['url'], "URL is empty")
        self.assertNotEqual(message['referer_url'], '', "Refer URL is empty")
        self.assertIsNotNone(message['sentiment'], "Sentiment is empty")
        self.assertIsNotNone(message['polarity'], "Polarity is empty")

if __name__ == '__main__':
    unittest.main()