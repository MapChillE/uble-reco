from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
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
            .options(joinedload(Store.brand).joinedload(Brand.Category))
            .all()
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
    count = 0

    embeddings_to_update = []
    embeddings_to_insert = []

    for store in stores:
        brand = store.brand

        category_name = brand.category.name if brand.category else ""
        combined_text = f"{brand.name or ''}. {brand.description or ''}. {category_name}"

        vec = model.encode(combined_text).tolist()

        existing = db.query(StoreEmbedding).filter(StoreEmbedding.store_id == store.id).first()
        if existing:
            embeddings_to_update.append({
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
        db.bult_save_objects(embeddings_to_insert)

    db.commit()
    return {"message": f"{count} store vectors created or updated"}

@router.post("/vectors/brand")
def generate_brand_vectors(db: Session = Depends(get_db)):
    brands = db.query(Brand).filter(Brand.description.isnot(None)).all()
    count = 0

    for brand in brands:
        category_name = brand.category.name if brand.category else ""
        combined_text = f"{brand.name or ''}. {brand.description or ''}. {category_name}"
        vec = model.encode(combined_text).tolist()

        existing = db.query(BrandEmbedding).filter(BrandEmbedding.brand_id == brand.id).first()
        if existing:
            existing.embedding = vec
            existing.updated_at = datetime.utcnow()
        else:
            db.add(BrandEmbedding(
                brand_id=brand.id,
                embedding=vec,
                updated_at=datetime.utcnow()
            ))
        count += 1
    db.commit()
    return {"message": f"{count} brand vectors created or updated"}

        