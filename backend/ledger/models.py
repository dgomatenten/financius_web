import uuid

from django.conf import settings
from django.db import models


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="categories"
    )
    external_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    name = models.CharField(max_length=255)
    # Self-referential FK; stored as UUID string in legacy SQLite — use FK here for integrity
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children"
    )
    display_order = models.IntegerField(default=0)
    is_engel = models.BooleanField(default=False)
    needs_wants = models.CharField(max_length=50, default="needs")
    is_housing = models.BooleanField(default=False)
    is_fixed_expense = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "categories"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "parent", "name"], name="uq_category_name_scope"
            )
        ]
        ordering = ["display_order", "name"]

    def __str__(self) -> str:
        return f"Category({self.name})"


class Shop(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shops"
    )
    external_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=512, null=True, blank=True)
    normalized_name = models.CharField(max_length=255, null=True, blank=True)
    default_category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="default_for_shops", db_column="default_category_id"
    )
    # Self-referential: shop merged into another shop
    merged_into_shop = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="merged_shops", db_column="merged_into_shop_id"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "shops"
        constraints = [
            models.UniqueConstraint(fields=["user", "name"], name="uq_shop_name_per_user")
        ]
        ordering = ["name"]

    def __str__(self) -> str:
        return f"Shop({self.name})"


class PaymentCard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payment_cards"
    )
    external_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    nickname = models.CharField(max_length=255)
    card_type = models.CharField(max_length=50)
    network = models.CharField(max_length=50, null=True, blank=True)
    color_hex = models.CharField(max_length=7, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "payment_cards"
        ordering = ["nickname"]

    def __str__(self) -> str:
        return f"PaymentCard({self.nickname})"


class CategoryMapping(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="category_mappings"
    )
    shop = models.ForeignKey(
        Shop, on_delete=models.CASCADE, related_name="category_mappings"
    )
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="category_mappings"
    )
    confidence = models.FloatField(default=0.5)
    source = models.CharField(max_length=50, default="user")
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "category_mappings"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "shop"], name="uq_mapping_shop_per_user"
            )
        ]

    def __str__(self) -> str:
        return f"CategoryMapping({self.shop} -> {self.category})"


class Receipt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="receipts"
    )
    external_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    shop = models.ForeignKey(
        Shop, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="receipts", db_column="shop_id"
    )
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="receipts", db_column="category_id"
    )
    payment_card = models.ForeignKey(
        PaymentCard, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="receipts", db_column="payment_card_id"
    )
    receipt_date = models.DateTimeField()
    currency = models.CharField(max_length=10)
    subtotal = models.FloatField(default=0)
    tax_amount = models.FloatField(default=0)
    total_amount = models.FloatField(default=0)
    note = models.TextField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "receipts"
        indexes = [models.Index(fields=["user", "receipt_date"], name="ix_receipts_user_date")]
        ordering = ["-receipt_date"]

    def __str__(self) -> str:
        return f"Receipt({self.id}, {self.receipt_date:%Y-%m-%d})"


class ReceiptLineItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    receipt = models.ForeignKey(
        Receipt, on_delete=models.CASCADE, related_name="line_items"
    )
    name = models.CharField(max_length=255)
    quantity = models.FloatField(default=1)
    unit_price = models.FloatField(default=0)
    line_total = models.FloatField(default=0)

    class Meta:
        db_table = "receipt_line_items"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"LineItem({self.name}, {self.line_total})"


class Budget(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="budgets"
    )
    year_month = models.CharField(max_length=7)  # e.g. "2024-01"
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="budgets", db_column="category_id"
    )
    mode = models.CharField(max_length=50)
    amount = models.FloatField(default=0)
    adjustment_pct = models.IntegerField(null=True, blank=True)
    rollover_enabled = models.BooleanField(default=False)
    rollover_balance = models.FloatField(default=0)

    class Meta:
        db_table = "budgets"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "year_month", "category"], name="uq_budget_scope"
            )
        ]
        ordering = ["-year_month"]

    def __str__(self) -> str:
        return f"Budget({self.year_month}, {self.amount})"


class PairingToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="pairing_tokens", db_index=True
    )
    token_hash = models.CharField(max_length=512, unique=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "pairing_tokens"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"PairingToken(user={self.user_id}, expires={self.expires_at:%Y-%m-%d})"


class SyncEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sync_events"
    )
    device_id = models.CharField(max_length=255)
    sync_started_at = models.DateTimeField()
    sync_completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50, default="success")
    receipts_count = models.IntegerField(default=0)
    line_items_count = models.IntegerField(default=0)
    categories_count = models.IntegerField(default=0)
    shops_count = models.IntegerField(default=0)
    cards_count = models.IntegerField(default=0)
    duplicates_count = models.IntegerField(default=0)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "sync_events"
        ordering = ["-sync_started_at"]

    def __str__(self) -> str:
        return f"SyncEvent(user={self.user_id}, status={self.status})"


class RecurringExpenseTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="recurring_expense_templates"
    )
    name = models.CharField(max_length=255)
    expected_amount = models.FloatField(default=0)
    frequency = models.CharField(max_length=50)
    start_date = models.DateTimeField()

    class Meta:
        db_table = "recurring_expense_templates"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"RecurringExpenseTemplate({self.name})"


class RecurringExpenseOccurrence(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(
        RecurringExpenseTemplate, on_delete=models.CASCADE, related_name="occurrences"
    )
    due_date = models.DateTimeField()
    status = models.CharField(max_length=50, default="upcoming")

    class Meta:
        db_table = "recurring_expense_occurrences"
        ordering = ["due_date"]

    def __str__(self) -> str:
        return f"RecurringExpenseOccurrence({self.template.name}, {self.due_date:%Y-%m-%d})"


class AmortizationRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="amortization_rules"
    )
    title = models.CharField(max_length=255)
    total_amount = models.FloatField(default=0)
    months = models.IntegerField(default=12)
    monthly_amount = models.FloatField(default=0)
    status = models.CharField(max_length=50, default="active")

    class Meta:
        db_table = "amortization_rules"
        ordering = ["title"]

    def __str__(self) -> str:
        return f"AmortizationRule({self.title})"
