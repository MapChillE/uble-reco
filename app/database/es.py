from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import os

load_dotenv()

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")
ES_ID = os.getenv("ES_ID")
ES_PW = os.getenv("ES_PW")

es = Elasticsearch(
            ELASTICSEARCH_URL, 
            basic_auth=(ES_ID, ES_PW),
            verify_certs=False
    )   