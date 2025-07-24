from elasticsearch import Elasticsearch
from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger(__name__)

load_dotenv()

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")
ES_ID = os.getenv("ES_ID")
ES_PW = os.getenv("ES_PW")

if not all([ELASTICSEARCH_URL, ES_ID, ES_PW]):
        raise ValueError("필수 Elasticsearch 환경 변수가 설정되지 않았습니다.")

es = Elasticsearch(
            ELASTICSEARCH_URL, 
            basic_auth=(ES_ID, ES_PW),
            verify_certs=True
    )   

#연결 확인
try:
        if not es.ping():
                raise ConnectionError("Elasticsearch 서버에 연결할 수 없습니다.")
        logger.info("Elasticsearch 연결 성공")
except Exception as e:
        logger.error(f"Elasticsearch 연결 실패: {e}")
        raise