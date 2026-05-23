from typing import Any
from datetime import datetime
from uuid import uuid4

from config.database import SessionLocal
from models.category import Category
from models.receipt import Receipt
from utils.exceptions import ValidationError


class CategoryService:
    def __init__(self, db_session=None):
        self.db = db_session or SessionLocal

    def list_tree(self, user_id: str) -> list[dict[str, Any]]:
        categories = (
            self.db.query(Category)
            .filter(Category.user_id == user_id, Category.is_deleted == False)  # noqa: E712
            .order_by(Category.display_order.asc(), Category.name.asc())
            .all()
        )

        nodes = {cat.id: self._to_dict(cat) for cat in categories}
        roots: list[dict[str, Any]] = []
        for category in categories:
            node = nodes[category.id]
            parent_id = category.parent_id
            if parent_id and parent_id in nodes:
                nodes[parent_id]["children"].append(node)
            else:
                roots.append(node)
        return roots

    def create_category(self, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        name = (payload.get("name") or "").strip()
        if not name:
            raise ValidationError("name is required")

        parent_id = payload.get("parentId")
        if parent_id:
            parent = self.db.query(Category).filter(Category.user_id == user_id, Category.id == parent_id).first()
            if not parent or parent.is_deleted:
                raise ValidationError("parentId is invalid")

        category = Category(
            id=str(uuid4()),
            user_id=user_id,
            name=name,
            parent_id=parent_id,
            display_order=int(payload.get("displayOrder", 0) or 0),
            is_engel=bool(payload.get("isEngel", False)),
            needs_wants=str(payload.get("needsWants", "needs")),
            is_housing=bool(payload.get("isHousing", False)),
            is_fixed_expense=bool(payload.get("isFixedExpense", False)),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return self._to_dict(category)

    def update_category(self, user_id: str, category_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        category = self._get_category(user_id, category_id)
        if not category or category.is_deleted:
            raise ValidationError("category not found")

        if "name" in payload:
            name = (payload.get("name") or "").strip()
            if not name:
                raise ValidationError("name cannot be empty")
            category.name = name

        if "parentId" in payload:
            parent_id = payload.get("parentId")
            if parent_id == category.id:
                raise ValidationError("category cannot be its own parent")
            if parent_id:
                parent = self._get_category(user_id, parent_id)
                if not parent or parent.is_deleted:
                    raise ValidationError("parentId is invalid")
                self._assert_no_cycle(user_id, category.id, parent_id)
            category.parent_id = parent_id

        if "displayOrder" in payload:
            category.display_order = int(payload.get("displayOrder") or 0)
        if "isEngel" in payload:
            category.is_engel = bool(payload.get("isEngel"))
        if "needsWants" in payload:
            category.needs_wants = str(payload.get("needsWants") or "needs")
        if "isHousing" in payload:
            category.is_housing = bool(payload.get("isHousing"))
        if "isFixedExpense" in payload:
            category.is_fixed_expense = bool(payload.get("isFixedExpense"))

        category.updated_at = datetime.utcnow()
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return self._to_dict(category)

    def delete_category(self, user_id: str, category_id: str) -> None:
        category = self._get_category(user_id, category_id)
        if not category or category.is_deleted:
            raise ValidationError("category not found")

        has_receipts = (
            self.db.query(Receipt)
            .filter(Receipt.user_id == user_id, Receipt.category_id == category_id)
            .first()
            is not None
        )
        if has_receipts:
            raise ValidationError("category has receipts; reassign before deletion")

        category.is_deleted = True
        category.updated_at = datetime.utcnow()
        self.db.add(category)
        self.db.commit()

    def _get_category(self, user_id: str, category_id: str) -> Category | None:
        return (
            self.db.query(Category)
            .filter(Category.user_id == user_id, Category.id == category_id)
            .first()
        )

    def _assert_no_cycle(self, user_id: str, category_id: str, new_parent_id: str) -> None:
        cursor = new_parent_id
        visited: set[str] = set()
        while cursor:
            if cursor == category_id:
                raise ValidationError("parentId would create a cycle")
            if cursor in visited:
                break
            visited.add(cursor)
            parent = self._get_category(user_id, cursor)
            cursor = parent.parent_id if parent else None

    def _to_dict(self, category: Category) -> dict[str, Any]:
        return {
            "id": category.id,
            "name": category.name,
            "parentId": category.parent_id,
            "displayOrder": category.display_order,
            "isEngel": category.is_engel,
            "needsWants": category.needs_wants,
            "isHousing": category.is_housing,
            "isFixedExpense": category.is_fixed_expense,
            "children": [],
        }
