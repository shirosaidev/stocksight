import argparse

from Sentiment.Initializer.ElasticSearchInit import es
from Sentiment.Initializer.LoggerInit import *

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--delindex", action="store_true",
                    help="Delete existing Elasticsearch index first")
    args = parser.parse_args()

    eslogger = logging.getLogger('elasticsearch')
    eslogger.setLevel(logging.INFO)

    if args.delindex:
        eslogger.info('Deleting existing Elasticsearch index ' + args.index)
        es.indices.delete(index=args.index, ignore=[400, 404])
