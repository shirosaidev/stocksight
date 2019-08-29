try:
    from elasticsearch5 import Elasticsearch
except ImportError:
    from elasticsearch import Elasticsearch

from config import elasticsearch_host, elasticsearch_port, elasticsearch_user, elasticsearch_password

# create instance of elasticsearch
es = Elasticsearch(hosts=[{'host': elasticsearch_host, 'port': elasticsearch_port}],
                   http_auth=(elasticsearch_user, elasticsearch_password))