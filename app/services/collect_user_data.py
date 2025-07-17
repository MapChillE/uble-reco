from sqlalchemy.orm import Session
from sqlalchemy import text

def collect_user_data(user_id: int, db: Session) -> tuple[list, list, list, list, list]:
    """Collect user-related text data from various sources."""
    categories = db.execute(text("""
        SELECT c.name FROM user_category uc
        JOIN category c ON uc.category_id = c.id
        WHERE uc.user_id = :user_id
    """), {"user_id": user_id}).scalars().all()

    histories = db.execute(text("""
        SELECT s.name FROM usage_history uh
        JOIN store s ON uh.store_id = s.id
        WHERE uh.user_id = :user_id
    """), {"user_id": user_id}).scalars().all()

    bookmarks = db.execute(text("""
        SELECT b.description FROM bookmark bm
        JOIN brand b ON bm.brand_id = b.id
        WHERE bm.user_id = :user_id
    """), {"user_id": user_id}).scalars().all()

    clicks = db.execute(text("""
        SELECT s.name FROM store_click_log cl
        JOIN store s ON cl.store_id = s.id
        WHERE cl.user_id = :user_id
    """), {"user_id": user_id}).scalars().all()

    searches = db.execute(text("""
        SELECT keyword FROM search_log WHERE user_id = :user_id
    """), {"user_id": user_id}).scalars().all()
    
    return categories, histories, bookmarks, clicks, searches