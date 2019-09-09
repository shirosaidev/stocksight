# set up elasticsearch mappings and create index
mapping = {
    "mappings": {
        "properties": {
            "author": {
                "type": "keyword",
            },
            "referer_url": {
                "type": "keyword",
            },
            "url": {
                "type": "text",
            },
            "location": {
                "type": "keyword",
            },
            "date": {
                "type": "date"
            },
            "title": {
                "type": "text",
            },
            "message": {
                "type": "text",
            },
            "msg_id": {
                "type": "keyword"
            },
            "polarity": {
                "type": "float"
            },
            "subjectivity": {
                "type": "float"
            },
            "sentiment": {
                "type": "keyword",
            }
        }
    },
    "settings": {
        "index": {
            "number_of_replicas": "0"
        }
    }
}

