from sqlalchemy import Column, BigInteger, String, TIMESTAMP, ForeignKey, Boolean, Date, Integer, Text
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from app.database.connection import Base

class Brand(Base):
    __tablename__="brand"
    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP)
    modified_at = Column(TIMESTAMP)
    csr_number = Column(String)
    description = Column(String)
    image_url = Column(String)
    is_local = Column(Boolean)
    is_online = Column(Boolean)
    name = Column(String)
    rank_type = Column(String)
    reservation_url = Column(String)
    season = Column(String)

    category_id = Column(BigInteger, ForeignKey("category.id"))
    category = relationship("Category")

    benefits = relationship("Benefit", back_populates="brand")
    stores = relationship("Store", back_populates="brand")
    bookmarks = relationship("Bookmark", back_populates="brand")
    click_logs = relationship("BrandClickLog", back_populates="brand", cascade="all, delete-orphan")
    embedding = relationship("BrandEmbedding", uselist=False, back_populates="brand")

class Benefit(Base):
    __tablename__ = "benefit"

    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP)
    modified_at = Column(TIMESTAMP)
    content = Column(String)
    manual = Column(Text)
    number = Column(Integer)
    period = Column(String)
    rank = Column(String)
    brand_id = Column(BigInteger, ForeignKey("brand.id"))

    brand = relationship("Brand", back_populates="benefits")
    usage_counts = relationship("UsageCount", back_populates="benefit")


class Category(Base):
    __tablename__="category"

    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP)
    modified_at = Column(TIMESTAMP)
    name = Column(String)


class Store(Base):
    __tablename__ = "store"

    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP)
    modified_at = Column(TIMESTAMP)
    address = Column(String)
    location = Column(Geography(geometry_type='POINT', srid=4326))
    name = Column(String)
    phone_number = Column(String)
    brand_id = Column(BigInteger, ForeignKey("brand.id"))

    brand = relationship("Brand", back_populates="stores")
    usage_histories = relationship("UsageHistory", back_populates="store")
    embedding_info = relationship("StoreEmbedding", back_populates="store", uselist=False)
    click_logs = relationship("StoreClickLog", back_populates="store", cascade="all, delete-orphan")

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP)
    modified_at = Column(TIMESTAMP)
    birth_date = Column(Date)
    gender = Column(String)
    is_deleted = Column(Boolean)
    is_vip_available = Column(Boolean)
    nickname = Column(String)
    provider_id = Column(String)
    rank = Column(String)
    role = Column(String)

    bookmarks = relationship("Bookmark", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")
    pins = relationship("Pin", back_populates="user")
    tokens = relationship("Token", back_populates="user", uselist=False)
    usage_histories = relationship("UsageHistory", back_populates="user")
    user_categories = relationship("UserCategory", back_populates="user")
    usage_counts = relationship("UsageCount", back_populates="user")
    brand_click_logs = relationship("BrandClickLog", back_populates="user", cascade="all, delete-orphan")
    store_click_logs = relationship("StoreClickLog", back_populates="user", cascade="all, delete-orphan")

class Bookmark(Base):
    __tablename__ = "bookmark"

    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP)
    modified_at = Column(TIMESTAMP)
    brand_id = Column(BigInteger, ForeignKey("brand.id"))
    user_id = Column(BigInteger, ForeignKey("users.id"))

    brand = relationship("Brand", back_populates="bookmarks")
    user = relationship("User", back_populates="bookmarks")


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP)
    modified_at = Column(TIMESTAMP)
    content = Column(String)
    title = Column(String)
    user_id = Column(BigInteger, ForeignKey("users.id"))

    user = relationship("User", back_populates="feedbacks")


class Pin(Base):
    __tablename__ = "pin"

    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP)
    modified_at = Column(TIMESTAMP)
    location = Column(Geography(geometry_type='POINT', srid=4326))
    name = Column(String)
    user_id = Column(BigInteger, ForeignKey("users.id"))

    user = relationship("User", back_populates="pins")


class Token(Base):
    __tablename__ = "token"

    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP)
    modified_at = Column(TIMESTAMP)
    expiry_date = Column(TIMESTAMP)
    refresh_token = Column(String)
    user_id = Column(BigInteger, ForeignKey("users.id"), unique=True)

    user = relationship("User", back_populates="tokens")


class UsageCount(Base):
    __tablename__ = "usage_count"

    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP)
    modified_at = Column(TIMESTAMP)
    count = Column(Integer)
    isavailable = Column(Boolean)
    benefit_id = Column(BigInteger, ForeignKey("benefit.id"))
    user_id = Column(BigInteger, ForeignKey("users.id"))

    benefit = relationship("Benefit", back_populates="usage_counts")
    user = relationship("User", back_populates="usage_counts")


class UsageHistory(Base):
    __tablename__ = "usage_history"

    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP)
    modified_at = Column(TIMESTAMP)
    store_id = Column(BigInteger, ForeignKey("store.id"))
    user_id = Column(BigInteger, ForeignKey("users.id"))

    store = relationship("Store", back_populates="usage_histories")
    user = relationship("User", back_populates="usage_histories")


class UserCategory(Base):
    __tablename__ = "user_category"

    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP)
    modified_at = Column(TIMESTAMP)
    category_id = Column(BigInteger, ForeignKey("category.id"))
    user_id = Column(BigInteger, ForeignKey("users.id"))

    user = relationship("User", back_populates="user_categories")


class StoreEmbedding(Base):
    __tablename__ = "store_embedding"

    store_id = Column(BigInteger, ForeignKey("store.id"), primary_key=True)
    embedding = Column(Vector(384))
    updated_at = Column(TIMESTAMP)

    store = relationship("Store", back_populates = "embedding_info")

class BrandEmbedding(Base):
    __tablename__ = "brand_embedding"

    id = Column(BigInteger, primary_key=True, index=True)
    brand_id = Column(BigInteger, ForeignKey("brand.id"), unique=True, nullable=False)
    embedding = Column(Vector(384))
    updated_at = Column(TIMESTAMP)

    brand = relationship("Brand", back_populates="embedding")

class BrandClickLog(Base):
    __tablename__ = "brand_click_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    brand_id = Column(BigInteger, ForeignKey("brand.id"), nullable=False)
    created_at = Column(TIMESTAMP)

    user = relationship("User", back_populates="brand_click_logs")
    brand = relationship("Brand", back_populates="click_logs")


class StoreClickLog(Base):
    __tablename__ = "store_click_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    store_id = Column(BigInteger, ForeignKey("store.id"), nullable=False)
    created_at = Column(TIMESTAMP)

    user = relationship("User", back_populates="store_click_logs")
    store = relationship("Store", back_populates="click_logs")


class SearchLog(Base):
    __tablename__ = "search_log"

    id = Column(BigInteger, primary_key=True)
    created_at = Column(TIMESTAMP)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    keyword = Column(String)

    user = relationship("User")