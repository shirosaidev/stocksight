try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse
import requests
from bs4 import BeautifulSoup
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from Initializer.LoggerInit import *


def get_page_text(url):

    max_paragraphs = 10

    try:
        logger.debug(url)
        req = requests.get(url)
        html = req.text
        soup = BeautifulSoup(html, 'html.parser')
        html_p = soup.findAll('p')

        logger.debug(html_p)

        if html_p:
            n = 1
            for i in html_p:
                if n <= max_paragraphs:
                    if i.string is not None:
                        logger.debug(i.string)
                        yield i.string
                n += 1

    except requests.exceptions.RequestException as re:
        logger.warning("Exception: can't crawl web site (%s)" % re)
        pass


def get_sentiment_from_url(text, sentimentURL):
    payload = {'text': text}

    try:
        post = requests.post(sentimentURL, data=payload)
        logger.debug(post.status_code)
        logger.debug(post.text)
    except requests.exceptions.RequestException as re:
        logger.error("Exception: requests exception getting sentiment from url caused by %s" % re)
        raise

    # return None if we are getting throttled or other connection problem
    if post.status_code != 200:
        logger.warning("Can't get sentiment from url caused by %s %s" % (post.status_code, post.text))
        return None

    response = post.json()
    logger.debug(response)

    # neg = response['probability']['neg']
    # neutral = response['probability']['neutral']
    # pos = response['probability']['pos']
    label = response['label']

    # determine if sentiment is positive, negative, or neutral
    if label == "neg":
        sentiment = "negative"
    elif label == "neutral":
        sentiment = "neutral"
    else:
        sentiment = "positive"

    return sentiment


def sentiment_analysis(text):
    """Determine if sentiment is positive, negative, or neutral
    algorithm to figure out if sentiment is positive, negative or neutral
    uses sentiment polarity from TextBlob, VADER Sentiment and
    sentiment from text-processing URL
    could be made better :)
    """
    sentimentURL = 'http://text-processing.com/api/sentiment/'
    # pass text into sentiment url
    sentiment_url = get_sentiment_from_url(text, sentimentURL)

    # pass text into TextBlob
    text_tb = TextBlob(text)

    # pass text into VADER Sentiment
    analyzer = SentimentIntensityAnalyzer()
    text_vs = analyzer.polarity_scores(text)

    if sentiment_url is None:
        if text_tb.sentiment.polarity <= 0 and text_vs['compound'] <= -0.5:
            sentiment = "negative"  # very negative
        elif text_tb.sentiment.polarity <= 0 and text_vs['compound'] <= -0.1:
            sentiment = "negative"  # somewhat negative
        elif text_tb.sentiment.polarity == 0 and text_vs['compound'] > -0.1 and text_vs['compound'] < 0.1:
            sentiment = "neutral"
        elif text_tb.sentiment.polarity >= 0 and text_vs['compound'] >= 0.1:
            sentiment = "positive"  # somewhat positive
        elif text_tb.sentiment.polarity > 0 and text_vs['compound'] >= 0.1:
            sentiment = "positive"  # very positive
        else:
            sentiment = "neutral"
    else:
        if text_tb.sentiment.polarity < 0 and text_vs['compound'] <= -0.1 and sentiment_url == "negative":
            sentiment = "negative"  # very negative
        elif text_tb.sentiment.polarity <= 0 and text_vs['compound'] < 0 and sentiment_url == "neutral":
            sentiment = "negative"  # somewhat negative
        elif text_tb.sentiment.polarity >= 0 and text_vs['compound'] > 0 and sentiment_url == "neutral":
            sentiment = "positive"  # somewhat positive
        elif text_tb.sentiment.polarity > 0 and text_vs['compound'] >= 0.1 and sentiment_url == "positive":
            sentiment = "positive"  # very positive
        else:
            sentiment = "neutral"

    # calculate average polarity from TextBlob and VADER
    polarity = (text_tb.sentiment.polarity + text_vs['compound']) / 2
    # output sentiment polarity
    print("Sentiment Polarity: " + str(polarity))

    # output sentiment subjectivity (TextBlob)
    print("Sentiment Subjectivity: " + str(text_tb.sentiment.subjectivity))

    # output sentiment
    print("Sentiment (url): " + str(sentiment_url))
    print("Sentiment (algorithm): " + str(sentiment))

    return polarity, text_tb.sentiment.subjectivity, sentiment