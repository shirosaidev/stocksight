"""Convert saved Xquik tweet results into StockSight documents."""

from datetime import datetime


def _tweet_items(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("tweets"), list):
        return payload["tweets"]
    return []


def iter_xquik_tweets(payload):
    """Yield valid objects from a Search Tweets response or tweets array."""
    for tweet in _tweet_items(payload):
        if isinstance(tweet, dict):
            yield tweet


def _first_string(*values):
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _first_value(mapping, *keys):
    for key in keys:
        value = mapping.get(key)
        if value is not None:
            return value
    return None


def _to_int(value, default=0):
    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _date(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return datetime.utcfromtimestamp(value).isoformat()
        except (OverflowError, OSError, ValueError):
            return ""

    if isinstance(value, str) and value.strip():
        cleaned = value.strip()
        for date_format in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                return datetime.strptime(cleaned, date_format).isoformat()
            except ValueError:
                pass

    return ""


def tweet_to_stocksight_document(
    tweet,
    clean_text,
    clean_text_sentiment,
    sentiment_analysis,
):
    """Convert one documented Xquik tweet into a StockSight document."""
    if not isinstance(tweet, dict):
        return None

    author = tweet.get("author") or {}
    if not isinstance(author, dict):
        author = {}

    text = _first_string(tweet.get("text"))
    tweet_id = _to_int(tweet.get("id"), None)
    created_at = _date(_first_value(tweet, "createdAt", "created"))
    if not text or tweet_id is None or not created_at:
        return None

    text_filtered = clean_text(text)
    text_clean = clean_text_sentiment(text_filtered)
    if not text_clean:
        return None

    polarity, subjectivity, sentiment = sentiment_analysis(text_clean)

    return {
        "author": _first_string(author.get("username")),
        "location": _first_string(author.get("location")),
        "language": _first_string(tweet.get("lang")),
        "friends": _to_int(author.get("following")),
        "followers": _to_int(author.get("followers")),
        "statuses": _to_int(_first_value(author, "statusesCount", "statuses_count")),
        "date": created_at,
        "message": text_filtered,
        "tweet_id": tweet_id,
        "polarity": polarity,
        "subjectivity": subjectivity,
        "sentiment": sentiment,
    }


def index_xquik_tweets(
    payload,
    index_document,
    clean_text,
    clean_text_sentiment,
    sentiment_analysis,
):
    """Convert and index valid tweets, returning indexed and skipped counts."""
    indexed = 0
    skipped = 0

    for tweet in iter_xquik_tweets(payload):
        document = tweet_to_stocksight_document(
            tweet,
            clean_text,
            clean_text_sentiment,
            sentiment_analysis,
        )
        if document is None:
            skipped += 1
            continue

        index_document(document)
        indexed += 1

    return indexed, skipped
