from datetime import datetime
from typing import Any

from config.database import SessionLocal
from models.master_data import CategoryMapping, Shop
from models.receipt import Receipt
from utils.exceptions import ValidationError


class ShopService:
    def __init__(self, db_session=None):
        self.db = db_session or SessionLocal

    def list_shops(self, user_id: str) -> list[dict[str, Any]]:
        shops = (
            self.db.query(Shop)
            .filter(Shop.user_id == user_id)
            .order_by(Shop.name.asc())
            .all()
        )
        return [
            {
                "id": shop.id,
                "name": shop.name,
                "address": shop.address,
                "isActive": shop.is_active,
                "mergedIntoShopId": shop.merged_into_shop_id,
            }
            for shop in shops
        ]

    def merge(self, user_id: str, primary: str, secondary: str) -> dict[str, str]:
        if not secondary:
            raise ValidationError("secondaryShopId is required")
        if primary == secondary:
            raise ValidationError("primary and secondary shop must differ")

        primary_shop = self._get_shop(user_id, primary)
        secondary_shop = self._get_shop(user_id, secondary)
        if not primary_shop or not secondary_shop:
            raise ValidationError("shop not found")

        self.db.query(Receipt).filter(
            Receipt.user_id == user_id,
            Receipt.shop_id == secondary_shop.id,
        ).update({"shop_id": primary_shop.id})

        self.db.query(CategoryMapping).filter(
            CategoryMapping.user_id == user_id,
            CategoryMapping.shop_id == secondary_shop.id,
        ).update({"shop_id": primary_shop.id, "updated_at": datetime.utcnow()})

        secondary_shop.merged_into_shop_id = primary_shop.id
        secondary_shop.is_active = False
        secondary_shop.updated_at = datetime.utcnow()
        self.db.add(secondary_shop)
        self.db.commit()

        return {"status": "merged"}

    def _get_shop(self, user_id: str, shop_id: str) -> Shop | None:
        return (
            self.db.query(Shop)
            .filter(Shop.user_id == user_id, Shop.id == shop_id)
            .first()
        )
