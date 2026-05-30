Scaffold a new Django model, DRF serializer, and/or viewset for the Financius Web project.

$ARGUMENTS format:  `<type> <name>`
  - type: `model`, `serializer`, `viewset`, or `all`
  - name: PascalCase name (e.g. `Receipt`, `Budget`)

If $ARGUMENTS is empty, ask the user which type and name they want.

---

## Project Conventions (MUST follow)

### 1. Response Envelope
Every API response MUST use this shape — Android Retrofit clients depend on it:
```python
{"data": ..., "error": None, "meta": {}}          # success
{"data": None, "error": {"code": "...", "message": "..."}, "meta": {}}  # error
```
Never return a bare dict or raise unhandled exceptions to the client.

### 2. Type Hints
All functions MUST have full type hints (PEP 8). No bare `except` clauses.

### 3. URL Prefix
All routes MUST sit under `/api/v1/`. Register in `backend/financius_web/urls.py`.

### 4. Auth
Protect endpoints with `IsAuthenticated`. Get the current user via `request.user`.

---

## Templates

### Model (`models.py` in the relevant Django app)
```python
import uuid
from django.db import models


class {{Name}}(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="{{name_plural}}"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = "{{table_name}}"       # match existing SQLite table name if migrating
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{{Name}}({self.id})"
```

After adding a model always run:
```bash
python3 manage.py makemigrations && python3 manage.py migrate
```

---

### Serializer (`serializers.py`)
```python
from rest_framework import serializers
from .models import {{Name}}


class {{Name}}Serializer(serializers.ModelSerializer):
    class Meta:
        model = {{Name}}
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at", "updated_at")
```

---

### ViewSet (`views.py`) — full CRUD with envelope
```python
import logging
from typing import Any

from django.db.models import QuerySet
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from .models import {{Name}}
from .serializers import {{Name}}Serializer

logger = logging.getLogger(__name__)


def _ok(data: Any, meta: dict | None = None) -> dict:
    return {"data": data, "error": None, "meta": meta or {}}


def _err(code: str, message: str) -> dict:
    return {"data": None, "error": {"code": code, "message": message}, "meta": {}}


class {{Name}}ViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def _queryset(self, request: Request) -> QuerySet:
        return {{Name}}.objects.filter(user=request.user, is_deleted=False)

    def list(self, request: Request) -> Response:
        qs = self._queryset(request)
        data = {{Name}}Serializer(qs, many=True).data
        logger.info("{{name}}.list user=%s count=%s", request.user.id, len(data))
        return Response(_ok({"items": data}))

    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        try:
            obj = self._queryset(request).get(pk=pk)
        except {{Name}}.DoesNotExist:
            return Response(_err("NOT_FOUND", "Not found."), status=status.HTTP_404_NOT_FOUND)
        return Response(_ok({{Name}}Serializer(obj).data))

    def create(self, request: Request) -> Response:
        serializer = {{Name}}Serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                _err("VALIDATION_ERROR", str(serializer.errors)),
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save(user=request.user)
        return Response(_ok(serializer.data), status=status.HTTP_201_CREATED)

    def update(self, request: Request, pk: str | None = None) -> Response:
        try:
            obj = self._queryset(request).get(pk=pk)
        except {{Name}}.DoesNotExist:
            return Response(_err("NOT_FOUND", "Not found."), status=status.HTTP_404_NOT_FOUND)
        serializer = {{Name}}Serializer(obj, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(
                _err("VALIDATION_ERROR", str(serializer.errors)),
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return Response(_ok(serializer.data))

    def destroy(self, request: Request, pk: str | None = None) -> Response:
        try:
            obj = self._queryset(request).get(pk=pk)
        except {{Name}}.DoesNotExist:
            return Response(_err("NOT_FOUND", "Not found."), status=status.HTTP_404_NOT_FOUND)
        obj.is_deleted = True
        obj.save(update_fields=["is_deleted", "updated_at"])
        return Response(_ok(None), status=status.HTTP_200_OK)
```

---

### URL Registration (`urls.py`)
```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import {{Name}}ViewSet

router = DefaultRouter()
router.register(r"{{url_prefix}}", {{Name}}ViewSet, basename="{{url_prefix}}")

urlpatterns = [
    path("api/v1/", include(router.urls)),
]
```

---

## Checklist after scaffolding

- [ ] `python3 manage.py makemigrations`
- [ ] `python3 manage.py migrate`
- [ ] Register URL in `financius_web/urls.py`
- [ ] Verify endpoint shape matches `{ data, error, meta }` envelope
- [ ] Check `db_table` matches existing SQLite table name (if migrating data)
- [ ] Add `djangorestframework` to `requirements.txt` if not present
