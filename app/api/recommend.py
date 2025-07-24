from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sentence_transformers import SentenceTransformer
from sqlalchemy import text, func
from app.database.connection import get_db
from app.models import Store, Brand
from app.services.recommend_service import HybridRecommender
from geoalchemy2.functions import ST_DWithin, ST_SetSRID, ST_MakePoint, ST_Distance
from geoalchemy2 import Geometry
from geoalchemy2.shape import to_shape
import logging
from app.services.collect_user_data import collect_user_data
from collections import defaultdict
from app.database.redis_client import r
import json
from app.database.es import es


router = APIRouter()
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
recommender = HybridRecommender()
logger = logging.getLogger(__name__)

def get_min_rank(benefits: list) -> str:
    for b in benefits:
        if b.rank != "NONE":
            return b.rank
    return "NONE"

def extract_lat_lng(store):
    if store.location is None:
        return None, None
    point = to_shape(store.location)
    return point.y, point.x

@router.get("/recommend")
def recommend(
    user_id:int, 
    lat: float = Query(...),
    lng: float = Query(...),
    radius_km: float = Query(2.0),
    db:Session = Depends(get_db)
    ):

    # 1. 사용자 정보 수집
    categories, histories, bookmarks, clicks, searches = collect_user_data(user_id, db, es)

    if not (categories or histories or bookmarks or clicks or searches):
        raise HTTPException(status_code=404, detail="사용자 정보가 부족합니다.")

    # 2. 텍스트 통합 후 임베딩
    user_profile_text = "; ".join(categories + histories + bookmarks + clicks + searches)
    user_vec = model.encode(user_profile_text).tolist()

    # 3. pgvector를 활용한 유사도 계산
    sql = text("""
        WITH click_counts AS (
        SELECT store_id, COUNT(*) AS click_count
        FROM store_click_log
        GROUP BY store_id
        ),
        click_stats AS (
            SELECT MAX(click_count) AS max_clicks,
                MIN(click_count) AS min_clicks
            FROM click_counts
        )
        SELECT s.id, s.name, s.address,
            1 - (embedding <-> CAST(:user_vec AS vector)) AS similarity,
            COALESCE(cc.click_count, 0) AS click_score,
            (SELECT COUNT(*) FROM usage_history WHERE store_id = s.id) AS visit_score,
            CASE 
                WHEN cs.max_clicks > cs.min_clicks THEN 
                    (COALESCE(cc.click_count, 0) - cs.min_clicks)::float / NULLIF(cs.max_clicks - cs.min_clicks, 0)
                ELSE 0
            END AS normalized_click_score
        FROM store_embedding se
        JOIN store s ON se.store_id = s.id
        LEFT JOIN click_counts cc ON cc.store_id = s.id
        CROSS JOIN click_stats cs
        WHERE ST_DWithin(s.location, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography, :radius)
        ORDER BY 0.7 * (1 - (embedding <-> CAST(:user_vec AS vector))) + 0.3 * (
            CASE 
                WHEN cs.max_clicks > cs.min_clicks THEN 
                    (COALESCE(cc.click_count, 0) - cs.min_clicks)::float / NULLIF(cs.max_clicks - cs.min_clicks, 0)
                ELSE 0
            END
        ) DESC
        LIMIT 10
    """)

    results = db.execute(sql, {
        "user_vec": user_vec,
        "lat": lat,
        "lng": lng,
        "radius": radius_km * 1000
    }).mappings().all()

    return {"top10": results}

@router.on_event("startup")
def startup_event():
    with next(get_db()) as db:
        recommender.train_model(db)

@router.get("/recommend/hybrid")
def hybrid_recommend(
    user_id: int, 
    lat: float = Query(37.5),
    lng: float = Query(127.04),
    radius_km: float = Query(2.0),
    db: Session = Depends(get_db)
):

    # 0. Redis 캐시 확인
    cache_key = f"recommendation:user:{user_id}"
    try:
        cached = r.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.error(f"Redis 캐시 확인 중 오류: {e}")

    # 1. 사용자 텍스트 정보 수집
    categories, histories, bookmarks, clicks, searches = collect_user_data(user_id, db, es)

    if not (categories or histories or bookmarks or clicks or searches):
        raise HTTPException(status_code=404, detail="사용자 정보가 부족합니다.")

    # 2. 벡터 생성
    user_profile_text = "; ".join(categories + histories + bookmarks + clicks + searches)
    user_vec = model.encode(user_profile_text).tolist()

    # 3. 추천 결과 계산
    results = recommender.get_hybrid_scores(db, user_id, user_vec)
    recommended_brand_ids = [brand_id for brand_id, _ in results]
    logger.debug(f"Recommendation results for user {user_id}: {results}")

    # 4. 위치 기반 필터링: 추천 브랜드 매장 중 반경 km 이내
    store_query = db.query(Store).options(
        joinedload(Store.brand).joinedload(Brand.category),
        joinedload(Store.brand).joinedload(Brand.benefits)
    ).filter(
        Store.brand_id.in_(recommended_brand_ids),
        func.ST_DWithin(Store.location, func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326), radius_km * 1000)
    ).order_by(
        func.ST_Distance(Store.location, func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326))
    ).all()

    # 매장 중 하나씩 결과 연결
    store_map = {}
    brand_store_map = defaultdict(list)
    for store in store_query:
        brand_store_map[store.brand_id].append(store)
    store_map = {bid: stores[0] for bid, stores in brand_store_map.items()}

    # 5. 결과 구성
    recommendation_items = []
    for brand_id, score in results:
        if brand_id not in store_map:
            continue
        store = store_map[brand_id]
        brand = store.brand
        lat, lng = extract_lat_lng(store)

        item = {
            "storeId": store.id,
            "storeName": store.name,
            "latitude": lat,
            "longitude": lng,
            "category": brand.category.name if brand.category else None,
            "description": brand.description,
            "isVIPcock": brand.rank_type in ("VIP", "VIP_NORMAL"),
            "minRank": get_min_rank(brand.benefits),
            "imgUrl": brand.image_url
        }
        recommendation_items.append(item)
    final_results = {"recommendationsList": recommendation_items}

    # 6. 캐시 저장 (1시간)
    try:
        r.setex(cache_key, 3600, json.dumps(final_results))
    except Exception as e:
        logger.error(f"Redis 캐싱 실패: {e}")

    # 7. 결과 반환
    return final_results
