from sqlalchemy.orm import Session
from sqlalchemy import text
from elasticsearch import Elasticsearch
from elasticsearch.helpers import scan
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def collect_user_data(user_id: int, db: Session, es: Elasticsearch) -> tuple[list, list, list, list, list]:
    
    #RDB에서 가져오는 데이터
    categories = db.execute(text("""
        SELECT c.name FROM user_category uc
        JOIN category c ON uc.category_id = c.id
        WHERE uc.user_id = :user_id
    """), {"user_id": user_id}).scalars().all()

    bookmarks = db.execute(text("""
        SELECT b.description FROM bookmark bm
        JOIN brand b ON bm.brand_id = b.id
        WHERE bm.user_id = :user_id
    """), {"user_id": user_id}).scalars().all()

    three_months_ago = (datetime.utcnow() - timedelta(days=90)).isoformat()

    # es에서 가져오는 이용 내역 로그
    histories = []
    try:
        for doc in scan(es, index="usage-history-log", query={
            "query": {
                "bool": {
                    "must": [
                        {"term": { "userId": user_id }},
                        {"range": { "createdAt": {"gte": three_months_ago}}}
                    ]
                }
            }

        }):
            store_name = doc["_source"].get("storeName")
            if store_name:
                histories.append(store_name)
    except Exception as e:
        logger.error(f"이용내역 로그 조회 실패 (user_id: {user_id}: {e})")

    # es에서 가져오는 클릭 로그
    clicks = []
    try:
        for doc in scan(es, index="store-click-log", query={
            "query": {
                "bool": {
                    "must": [
                        {"term": { "userId": user_id }},
                        {"range": { "createdAt": {"gte": three_months_ago}}}
                    ]
                }
            }
        }):
            store_name = doc["_source"].get("storeName")
            if store_name:
                clicks.append(store_name)
    except Exception as e:
        logger.error(f"클릭 로그 조회 실패 (user_id: {user_id}: {e})")

    # es에서 가져오는 검색 로그
    searches = []
    try:
        for doc in scan(es, index="search-log", query={
            "query": {
                "bool": {
                    "must": [
                        {"term": { "userId": user_id }},
                        {"range": { "createdAt": {"gte": three_months_ago}}}
                    ]
                }
            }       
        }):
            keyword = doc["_source"].get("searchKeyword")
            if keyword:
                searches.append(keyword)
    except Exception as e:
        logger.error(f"검색 로그 조회 실패 (user_id: {user_id}: {e})")

    return categories, histories, bookmarks, clicks, searches