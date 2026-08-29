"""Tests for Xquik JSON import helpers."""

import unittest
from pathlib import Path

from xquik_import import (
    index_xquik_tweets,
    iter_xquik_tweets,
    tweet_to_stocksight_document,
)


def _sentiment(_text):
    return 0.25, 0.5, "positive"


def _identity(text):
    return text


class TestXquikImport(unittest.TestCase):
    def test_docker_image_includes_xquik_importer(self):
        dockerfile = Path(__file__).resolve().parents[1] / "Dockerfile"

        self.assertIn("COPY xquik_import.py ./", dockerfile.read_text())

    def test_iter_xquik_tweets_accepts_documented_shapes(self):
        tweet = {"id": "1", "text": "TSLA update"}

        self.assertEqual(list(iter_xquik_tweets({"tweets": [tweet, "skip"]})), [tweet])
        self.assertEqual(list(iter_xquik_tweets([tweet, None])), [tweet])

    def test_iter_xquik_tweets_rejects_undocumented_envelopes(self):
        tweet = {"id": "1", "text": "TSLA update"}

        self.assertEqual(list(iter_xquik_tweets({"data": {"tweets": [tweet]}})), [])
        self.assertEqual(list(iter_xquik_tweets({"results": [tweet]})), [])

    def test_tweet_to_stocksight_document_maps_rest_fields(self):
        tweet = {
            "id": "123",
            "text": "TSLA ships a complete update",
            "createdAt": "2026-07-05T12:00:00Z",
            "lang": "en",
            "author": {
                "username": "example",
                "location": "Istanbul",
                "followers": 42,
                "following": 7,
                "statusesCount": 99,
            },
        }

        document = tweet_to_stocksight_document(tweet, _identity, _identity, _sentiment)

        self.assertEqual(
            document,
            {
                "author": "example",
                "location": "Istanbul",
                "language": "en",
                "friends": 7,
                "followers": 42,
                "statuses": 99,
                "date": "2026-07-05T12:00:00",
                "message": "TSLA ships a complete update",
                "tweet_id": 123,
                "polarity": 0.25,
                "subjectivity": 0.5,
                "sentiment": "positive",
            },
        )

    def test_tweet_to_stocksight_document_maps_mcp_fields(self):
        tweet = {
            "id": "123",
            "text": "TSLA ships a long update",
            "created": 1769817600,
            "author": {
                "username": "example",
                "followers": "42",
                "following": "7",
                "statuses_count": "99",
            },
        }

        document = tweet_to_stocksight_document(tweet, _identity, _identity, _sentiment)

        self.assertEqual(document["date"], "2026-01-31T00:00:00")
        self.assertEqual(document["message"], "TSLA ships a long update")
        self.assertEqual(document["followers"], 42)
        self.assertEqual(document["friends"], 7)
        self.assertEqual(document["statuses"], 99)

    def test_tweet_to_stocksight_document_skips_malformed_records(self):
        valid = {
            "id": "123",
            "text": "TSLA update",
            "createdAt": "2026-07-05T12:00:00Z",
        }

        for tweet in (
            None,
            {"text": "TSLA update", "createdAt": "2026-07-05T12:00:00Z"},
            {"id": "bad", "text": "TSLA update", "createdAt": "2026-07-05T12:00:00Z"},
            {"id": "123", "createdAt": "2026-07-05T12:00:00Z"},
            {"id": "123", "text": "TSLA update"},
            {"id": "123", "text": "TSLA update", "createdAt": "not-a-date"},
            {"id": True, "text": "TSLA update", "created": 1769817600},
            {"id": "123", "text": "TSLA update", "created": 10 ** 30},
        ):
            with self.subTest(tweet=tweet):
                self.assertIsNone(
                    tweet_to_stocksight_document(tweet, _identity, _identity, _sentiment)
                )

        self.assertIsNone(
            tweet_to_stocksight_document(valid, _identity, lambda _text: "", _sentiment)
        )

    def test_index_xquik_tweets_indexes_valid_documents_and_counts_skips(self):
        indexed = []
        payload = {
            "tweets": [
                {
                    "id": "123",
                    "text": "TSLA update",
                    "createdAt": "2026-07-05T12:00:00Z",
                },
                {"id": "bad", "text": "TSLA update"},
            ]
        }

        counts = index_xquik_tweets(
            payload,
            indexed.append,
            _identity,
            _identity,
            _sentiment,
        )

        self.assertEqual(counts, (1, 1))
        self.assertEqual(len(indexed), 1)
        self.assertEqual(indexed[0]["tweet_id"], 123)


if __name__ == "__main__":
    unittest.main()
