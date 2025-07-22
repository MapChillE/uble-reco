from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sentence_transformers import SentenceTransformer
from app.database.connection import get_db
from app.models import Store, Brand, StoreEmbedding, BrandEmbedding
from datetime import datetime

router = APIRouter()

model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

@router.post("/vectors/store")
def generate_store_vectors(db: Session = Depends(get_db)):
    try:
        stores = (
            db.query(Store)
            .join(Store.brand)
            .filter(Store.brand.has(Brand.description.isnot(None)))
            .options(joinedload(Store.brand).joinedload(Brand.category))
            .all()
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}") from e
    count = 0

    embeddings_to_update = []
    embeddings_to_insert = []

    store_ids = [store.id for store in stores]
    existing_embeddings = {
        emb.store_id: emb for emb in 
        db.query(StoreEmbedding).filter(StoreEmbedding.store_id.in_(store_ids)).all()
    }

    for store in stores:
        brand = store.brand

        category_name = brand.category.name if brand.category else ""
        combined_text = f"{brand.name or ''}. {brand.description or ''}. {category_name}"

        vec = model.encode(combined_text).tolist()

        existing = existing_embeddings.get(store.id)

        if existing:
            embeddings_to_update.append({
                'id': existing.id,
                'store_id': store.id,
                'embedding': vec,
                'updated_at': datetime.utcnow()
            })
        else:
            embeddings_to_insert.append(StoreEmbedding(
                store_id=store.id,
                embedding=vec,
                updated_at=datetime.utcnow()
            ))
        count += 1

    if embeddings_to_update:
        db.bulk_update_mappings(StoreEmbedding, embeddings_to_update)
    if embeddings_to_insert:
        db.bulk_save_objects(embeddings_to_insert)

    db.commit()
    return {"message": f"{count} store vectors created or updated"}

@router.post("/vectors/brand")
def generate_brand_vectors(db: Session = Depends(get_db)):
    try:
        brands = (
            db.query(Brand)
            .filter(Brand.description.isnot(None))
            .options(joinedload(Brand.category))
            .all()
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}") from e
    count = 0

    embeddings_to_update = []
    embeddings_to_insert = []

    brand_ids = [brand.id for brand in brands]
    existing_embeddings = {
        emb.brand_id: emb for emb in
        db.query(BrandEmbedding).filter(BrandEmbedding.brand_id.in_(brand_ids)).all()
    }

    for brand in brands:
        category_name = brand.category.name if brand.category else ""
        combined_text = f"{brand.name or ''}. {brand.description or ''}. {category_name}"

        vec = model.encode(combined_text).tolist()

        existing = existing_embeddings.get(brand.id)

        if existing:
            embeddings_to_update.append({
                'id': existing.id,
                'brand_id': brand.id,
                'embedding': vec,
                'updated_at': datetime.utcnow()
            })
        else:
            embeddings_to_insert.append(BrandEmbedding(
                brand_id=brand.id,
                embedding=vec,
                updated_at=datetime.utcnow()
            ))
        count += 1
    
    if embeddings_to_update:
        db.bulk_update_mappings(BrandEmbedding, embeddings_to_update)
    if embeddings_to_insert:
        db.bulk_save_objects(embeddings_to_insert)

    db.commit()
    return {"message": f"{count} brand vectors created or updated"}

        