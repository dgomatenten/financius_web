import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from ledger.models import Category, CategoryMapping, PaymentCard, Shop

User = get_user_model()


@pytest.mark.django_db
class TestCategoryModel:
    def test_create_category(self, user: User) -> None:
        cat = Category.objects.create(user=user, name="Food")
        assert cat.pk is not None
        assert cat.name == "Food"
        assert cat.is_deleted is False
        assert cat.parent is None

    def test_self_referential_parent(self, user: User) -> None:
        parent = Category.objects.create(user=user, name="Food")
        child = Category.objects.create(user=user, name="Groceries", parent=parent)
        assert child.parent == parent
        assert parent.children.first() == child

    def test_unique_constraint(self, user: User) -> None:
        # Constraint is (user, parent, name) — same parent required to trigger it.
        # Two categories with parent=None don't collide (NULL != NULL in SQL).
        parent = Category.objects.create(user=user, name="Top")
        Category.objects.create(user=user, name="Food", parent=parent)
        with pytest.raises(IntegrityError):
            Category.objects.create(user=user, name="Food", parent=parent)

    def test_soft_delete(self, user: User) -> None:
        cat = Category.objects.create(user=user, name="Food")
        cat.is_deleted = True
        cat.save()
        assert Category.objects.get(pk=cat.pk).is_deleted is True

    def test_db_table(self) -> None:
        assert Category._meta.db_table == "categories"

    def test_str(self, user: User) -> None:
        cat = Category.objects.create(user=user, name="Food")
        assert str(cat) == "Category(Food)"


@pytest.mark.django_db
class TestShopModel:
    def test_create_shop(self, user: User) -> None:
        shop = Shop.objects.create(user=user, name="Walmart")
        assert shop.pk is not None
        assert shop.is_active is True
        assert shop.default_category is None

    def test_unique_name_per_user(self, user: User) -> None:
        Shop.objects.create(user=user, name="Walmart")
        with pytest.raises(IntegrityError):
            Shop.objects.create(user=user, name="Walmart")

    def test_default_category_fk(self, user: User) -> None:
        cat = Category.objects.create(user=user, name="Groceries")
        shop = Shop.objects.create(user=user, name="Walmart", default_category=cat)
        assert shop.default_category == cat

    def test_merged_into_shop_self_fk(self, user: User) -> None:
        shop_a = Shop.objects.create(user=user, name="Old Shop")
        shop_b = Shop.objects.create(user=user, name="New Shop", merged_into_shop=shop_a)
        assert shop_b.merged_into_shop == shop_a

    def test_db_table(self) -> None:
        assert Shop._meta.db_table == "shops"

    def test_str(self, user: User) -> None:
        shop = Shop.objects.create(user=user, name="Walmart")
        assert str(shop) == "Shop(Walmart)"


@pytest.mark.django_db
class TestPaymentCardModel:
    def test_create_card(self, user: User) -> None:
        card = PaymentCard.objects.create(
            user=user, nickname="Chase Sapphire", card_type="credit"
        )
        assert card.pk is not None
        assert card.is_active is True
        assert card.network is None

    def test_db_table(self) -> None:
        assert PaymentCard._meta.db_table == "payment_cards"

    def test_str(self, user: User) -> None:
        card = PaymentCard.objects.create(
            user=user, nickname="Chase Sapphire", card_type="credit"
        )
        assert str(card) == "PaymentCard(Chase Sapphire)"


@pytest.mark.django_db
class TestCategoryMappingModel:
    def test_create_mapping(self, user: User) -> None:
        cat = Category.objects.create(user=user, name="Groceries")
        shop = Shop.objects.create(user=user, name="Walmart")
        mapping = CategoryMapping.objects.create(
            user=user, shop=shop, category=cat, confidence=0.9, source="user"
        )
        assert mapping.pk is not None
        assert mapping.confidence == 0.9

    def test_unique_shop_per_user(self, user: User) -> None:
        cat = Category.objects.create(user=user, name="Groceries")
        shop = Shop.objects.create(user=user, name="Walmart")
        CategoryMapping.objects.create(user=user, shop=shop, category=cat)
        with pytest.raises(IntegrityError):
            CategoryMapping.objects.create(user=user, shop=shop, category=cat)

    def test_cascade_on_shop_delete(self, user: User) -> None:
        cat = Category.objects.create(user=user, name="Groceries")
        shop = Shop.objects.create(user=user, name="Walmart")
        CategoryMapping.objects.create(user=user, shop=shop, category=cat)
        shop.delete()
        assert CategoryMapping.objects.filter(user=user).count() == 0

    def test_db_table(self) -> None:
        assert CategoryMapping._meta.db_table == "category_mappings"
