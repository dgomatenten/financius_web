from datetime import datetime, timezone

import pytest
from django.contrib.auth import get_user_model

from ledger.models import Category, PaymentCard, Receipt, ReceiptLineItem, Shop

User = get_user_model()


@pytest.fixture
def shop(user: User) -> Shop:
    return Shop.objects.create(user=user, name="Walmart")


@pytest.fixture
def category(user: User) -> Category:
    return Category.objects.create(user=user, name="Groceries")


@pytest.fixture
def card(user: User) -> PaymentCard:
    return PaymentCard.objects.create(user=user, nickname="Visa", card_type="credit")


@pytest.fixture
def receipt(user: User, shop: Shop, category: Category, card: PaymentCard) -> Receipt:
    return Receipt.objects.create(
        user=user,
        shop=shop,
        category=category,
        payment_card=card,
        receipt_date=datetime(2024, 1, 15, tzinfo=timezone.utc),
        currency="USD",
        subtotal=90.0,
        tax_amount=10.0,
        total_amount=100.0,
    )


@pytest.mark.django_db
class TestReceiptModel:
    def test_create_receipt(self, receipt: Receipt) -> None:
        assert receipt.pk is not None
        assert receipt.currency == "USD"
        assert receipt.total_amount == 100.0
        assert receipt.is_deleted is False

    def test_optional_fks_nullable(self, user: User) -> None:
        r = Receipt.objects.create(
            user=user,
            receipt_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            currency="USD",
            total_amount=50.0,
        )
        assert r.shop is None
        assert r.category is None
        assert r.payment_card is None

    def test_shop_fk(self, receipt: Receipt, shop: Shop) -> None:
        assert receipt.shop == shop
        assert shop.receipts.first() == receipt

    def test_category_fk(self, receipt: Receipt, category: Category) -> None:
        assert receipt.category == category

    def test_payment_card_fk(self, receipt: Receipt, card: PaymentCard) -> None:
        assert receipt.payment_card == card

    def test_soft_delete(self, receipt: Receipt) -> None:
        receipt.is_deleted = True
        receipt.save()
        assert Receipt.objects.get(pk=receipt.pk).is_deleted is True

    def test_cascade_on_user_delete(self, user: User, receipt: Receipt) -> None:
        receipt_id = receipt.pk
        user.delete()
        assert Receipt.objects.filter(pk=receipt_id).count() == 0

    def test_db_table(self) -> None:
        assert Receipt._meta.db_table == "receipts"

    def test_str(self, receipt: Receipt) -> None:
        assert "2024-01-15" in str(receipt)


@pytest.mark.django_db
class TestReceiptLineItemModel:
    def test_create_line_item(self, receipt: Receipt) -> None:
        item = ReceiptLineItem.objects.create(
            receipt=receipt,
            name="Milk",
            quantity=2,
            unit_price=3.5,
            line_total=7.0,
        )
        assert item.pk is not None
        assert item.line_total == 7.0

    def test_multiple_items_on_receipt(self, receipt: Receipt) -> None:
        ReceiptLineItem.objects.create(receipt=receipt, name="Milk", quantity=1, unit_price=3.5, line_total=3.5)
        ReceiptLineItem.objects.create(receipt=receipt, name="Bread", quantity=1, unit_price=2.5, line_total=2.5)
        assert receipt.line_items.count() == 2

    def test_cascade_on_receipt_delete(self, receipt: Receipt) -> None:
        ReceiptLineItem.objects.create(receipt=receipt, name="Milk", quantity=1, unit_price=3.5, line_total=3.5)
        receipt.delete()
        assert ReceiptLineItem.objects.count() == 0

    def test_db_table(self) -> None:
        assert ReceiptLineItem._meta.db_table == "receipt_line_items"

    def test_str(self, receipt: Receipt) -> None:
        item = ReceiptLineItem.objects.create(
            receipt=receipt, name="Milk", quantity=1, unit_price=3.5, line_total=3.5
        )
        assert "Milk" in str(item)
