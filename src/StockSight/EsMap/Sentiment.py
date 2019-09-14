# set up elasticsearch mappings and create index
mapping = {
    "mappings": {
        "properties": {
            "author": {
                "type": "text",
                "fields": {
                      "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                      }
                }
            },
            "referer_url": {
                "type": "text",
                "fields": {
                      "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                      }
                }
            },
            "url": {
                "type": "text",
                "fields": {
                      "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                      }
                }
            },
            "location": {
                "type": "text",
                "fields": {
                      "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                      }
                }
            },
            "date": {
                "type": "date"
            },
            "title": {
                "type": "text",
                "fields": {
                      "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                      }
                }
            },
            "message": {
                "type": "text",
            },
            "msg_id": {
                "type": "keyword",
            },
            "polarity": {
                "type": "float"
            },
            "subjectivity": {
                "type": "float"
            },
            "sentiment": {
                "type": "text",
                "fields": {
                      "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                      }
                }
            },
            "msg_polarity": {
                "type": "float"
            },
            "msg_subjectivity": {
                "type": "float"
            },
            "msg_sentiment": {
                "type": "text",
                "fields": {
                      "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                      }
                }
            }
        }
    },
    "settings": {
        "index": {
            "number_of_replicas": "0"
        }
    }
}

