# set up elasticsearch mappings and create index
mapping = {
    "mappings": {
        "properties": {
            "author": {
                "type": "keyword",
            },
            "location": {
                "type": "keyword",
            },
            "date": {
                "type": "date"
            },
            "message": {
                "type": "keyword",
            },
            "msg_id": {
                "type": "text"
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
    }
}

