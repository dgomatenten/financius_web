from flask import Blueprint, jsonify, request

from api.envelope import ok
from config.database import SessionLocal
from services.card_service import CardService
from services.category_mapping_service import CategoryMappingService
from services.category_service import CategoryService
from services.shop_service import ShopService
from utils.auth import get_current_user_id


bp = Blueprint("master_data", __name__)


@bp.get("/categories")
def list_categories() -> tuple:
    user_id = get_current_user_id()
    db = SessionLocal()
    try:
        category_service = CategoryService(db)
        return jsonify(ok(category_service.list_tree(user_id))), 200
    finally:
        db.close()


@bp.post("/categories")
def create_category() -> tuple:
    user_id = get_current_user_id()
    body = request.get_json(silent=True) or {}
    db = SessionLocal()
    try:
        category_service = CategoryService(db)
        return jsonify(ok(category_service.create_category(user_id, body))), 201
    finally:
        db.close()


@bp.patch("/categories/<category_id>")
def patch_category(category_id: str) -> tuple:
    user_id = get_current_user_id()
    body = request.get_json(silent=True) or {}
    db = SessionLocal()
    try:
        category_service = CategoryService(db)
        return jsonify(ok(category_service.update_category(user_id, category_id, body))), 200
    finally:
        db.close()


@bp.delete("/categories/<category_id>")
def delete_category(category_id: str) -> tuple:
    user_id = get_current_user_id()
    db = SessionLocal()
    try:
        category_service = CategoryService(db)
        category_service.delete_category(user_id, category_id)
        return jsonify(ok({"id": category_id, "deleted": True})), 200
    finally:
        db.close()


@bp.get("/shops")
def list_shops() -> tuple:
    user_id = get_current_user_id()
    db = SessionLocal()
    try:
        shop_service = ShopService(db)
        return jsonify(ok(shop_service.list_shops(user_id))), 200
    finally:
        db.close()


@bp.post("/shops/<shop_id>/merge")
def merge_shops(shop_id: str) -> tuple:
    user_id = get_current_user_id()
    body = request.get_json(silent=True) or {}
    db = SessionLocal()
    try:
        shop_service = ShopService(db)
        return jsonify(ok(shop_service.merge(user_id, shop_id, body.get("secondaryShopId", "")))), 200
    finally:
        db.close()


@bp.get("/cards")
def list_cards() -> tuple:
    user_id = get_current_user_id()
    db = SessionLocal()
    try:
        card_service = CardService(db)
        return jsonify(ok(card_service.list_cards(user_id))), 200
    finally:
        db.close()


@bp.post("/cards")
def create_card() -> tuple:
    user_id = get_current_user_id()
    body = request.get_json(silent=True) or {}
    db = SessionLocal()
    try:
        card_service = CardService(db)
        return jsonify(ok(card_service.create_card(user_id, body))), 201
    finally:
        db.close()


@bp.patch("/cards/<card_id>")
def deactivate_card(card_id: str) -> tuple:
    user_id = get_current_user_id()
    db = SessionLocal()
    try:
        card_service = CardService(db)
        return jsonify(ok(card_service.deactivate_card(user_id, card_id))), 200
    finally:
        db.close()


@bp.get("/category-mappings")
def list_mappings() -> tuple:
    user_id = get_current_user_id()
    db = SessionLocal()
    try:
        mapping_service = CategoryMappingService(db)
        return jsonify(ok(mapping_service.list_mappings(user_id))), 200
    finally:
        db.close()


@bp.patch("/category-mappings/<mapping_id>")
def correct_mapping(mapping_id: str) -> tuple:
    user_id = get_current_user_id()
    body = request.get_json(silent=True) or {}
    db = SessionLocal()
    try:
        mapping_service = CategoryMappingService(db)
        data = mapping_service.correct_mapping(user_id, mapping_id, body.get("categoryId", ""))
        return jsonify(ok(data)), 200
    finally:
        db.close()
