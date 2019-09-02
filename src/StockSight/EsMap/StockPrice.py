# set up elasticsearch mappings and create index
mapping = {
    "mappings": {
        "properties": {
            "symbol": {
                "type": "keyword"
            },
            "price_last": {
                "type": "float"
            },
            "date": {
                "type": "date"
            },
            "change": {
                "type": "float"
            },
            "price_high": {
                "type": "float"
            },
            "price_low": {
                "type": "float"
            },
            "vol": {
                "type": "integer"
            }
        }
    }
}