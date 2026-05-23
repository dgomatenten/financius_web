from datetime import datetime
from typing import Any

from config.database import SessionLocal
from models.master_data import CategoryMapping, Shop
from models.category import Category
from utils.exceptions import ValidationError


class CategoryMappingService:
    def __init__(self, db_session=None):
        self.db = db_session or SessionLocal

    def list_mappings(self, user_id: str) -> list[dict[str, Any]]:
        mappings = (
            self.db.query(CategoryMapping)
            .filter(CategoryMapping.user_id == user_id)
            .all()
        )
        result: list[dict[str, Any]] = []
        for mapping in mappings:
            shop = self.db.query(Shop).filter(Shop.id == mapping.shop_id).first()
            category = self.db.query(Category).filter(Category.id == mapping.category_id).first()
            result.append(
                {
                    "id": mapping.id,
                    "shopId": mapping.shop_id,
                    "shopName": shop.name if shop else None,
                    "categoryId": mapping.category_id,
                    "categoryName": category.name if category else None,
                    "confidence": mapping.confidence,
                    "source": mapping.source,
                }
            )
        return result

    def correct_mapping(self, user_id: str, mapping_id: str, category_id: str) -> dict[str, Any]:
        if not category_id:
            raise ValidationError("categoryId is required")

        mapping = (
            self.db.query(CategoryMapping)
            .filter(CategoryMapping.user_id == user_id, CategoryMapping.id == mapping_id)
            .first()
        )
        if not mapping:
            raise ValidationError("mapping not found")

        category = (
            self.db.query(Category)
            .filter(Category.user_id == user_id, Category.id == category_id, Category.is_deleted == False)  # noqa: E712
            .first()
        )
        if not category:
            raise ValidationError("category not found")

        mapping.category_id = category_id
        mapping.source = "user"
        mapping.updated_at = datetime.utcnow()
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)

        return {
            "id": mapping.id,
            "shopId": mapping.shop_id,
            "categoryId": mapping.category_id,
            "confidence": mapping.confidence,
            "source": mapping.source,
        }
