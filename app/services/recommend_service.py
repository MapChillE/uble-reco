import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from implicit.als import AlternatingLeastSquares
from sqlalchemy.orm import Session
from app.models import BrandClickLog, StoreClickLog, BrandEmbedding, Store, Brand
from app.database.connection import get_db

class HybridRecommender:
    def __init__(self):
        self.model = None
        self.user_factors = None
        self.item_factors = None
        self.item_id_to_index = {}
        self.index_to_item_id = {}

    def train_model(self, db: Session):
        store_logs = db.query(StoreClickLog).all()
        brand_logs = db.query(BrandClickLog).all()

        combined_data = []

        # Store 클릭 로그 : brand_id로 매핑
        for log in store_logs:
            store = db.query(Store).filter(Store.id == log.store_id).first()
            if store and store.brand_id:
                combined_data.append({'user_id': log.user_id, 'brand_id': store.brand_id})
        
        # Brand 클릭 로그
        for log in brand_logs:
            combined_data.append({'user_id': log.user_id, 'brand_id': log.brand_id}) 

        if not combined_data:
            return
        
        df = pd.DataFrame(combined_data)
        df['value'] = 1
        df = df.groupby(['user_id', 'brand_id']).size().reset_index(name='value')

        # 카테고리 코드화 
        df['user_code'] = df['user_id'].astype('category').cat.codes
        df['brand_code'] = df['brand_id'].astype('category').cat.codes

        # ID, 코드 매핑
        self.item_id_to_index = {
            brand_id: code for brand_id, code in zip(df['brand_id'], df['brand_code'])
        }
        self.index_to_item_id = {
            code: brand_id for brand_id, code in zip(df['brand_id'], df['brand_code'])
        }
        self.user_id_to_code = {
            user_id: code for user_id, code in zip(df['user_id'], df['user_code'])
        }
        self.code_to_user_id = {
            code: user_id for user_id, code in zip(df['user_id'], df['user_code'])
        }           

        # 희소행렬 생성 후 학습
        sparse_matrix = coo_matrix((df['value'], (df['user_code'], df['brand_code'])))
        self.model = AlternatingLeastSquares(factors=50, regularization=0.01, iterations=20)
        self.model.fit(sparse_matrix)

        self.user_factors = self.model.user_factors
        self.item_factors = self.model.item_factors

    def get_als_scores(self, user_id: int, top_k: int = 10):
        if not self.model or user_id not in self.user_id_to_code:
            return {}
        user_code = self.user_id_to_code[user_id]
        scores = self.model.recommend(userid=user_code, user_items=self.model.user_items[user_code], N=top_k, filter_already_liked_items=False)
        return {self.index_to_item_id[item_idx]: score for item_idx, score in scores}

    def get_vector_scores(self, db: Session, user_vec: list, top_k: int = 10):
        embeddings = db.query(BrandEmbedding).all()
        scores = []
        for e in embeddings:
            sim = np.dot(user_vec, e.embedding) / (np.linalg.norm(user_vec) * np.linalg.norm(e.embedding))
            scores.append((e.brand_id, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return dict(scores[:top_k])

    def get_hybrid_scores(
        self, 
        db: Session, 
        user_id: int, 
        user_vec: list, 
        top_k: int = 10
    ):
        als_scores = self.get_als_scores(user_id, top_k * 2)
        vec_scores = self.get_vector_scores(db, user_vec, top_k * 2)

        all_ids = set(als_scores.keys()) | set(vec_scores.keys())
        hybrid_scores = {}
        for bid in all_ids:
            als = als_scores.get(bid, 0)
            vec = vec_scores.get(bid, 0)
            hybrid_scores[bid] = 0.5 * als + 0.5 * vec

        sorted_scores = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)
        print("후보군!!")
        print(sorted_scores[:top_k])
        return sorted_scores[:top_k]