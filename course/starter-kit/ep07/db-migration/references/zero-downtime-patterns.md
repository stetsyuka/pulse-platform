# Патерни міграцій без простою для великих таблиць

Читати лише для таблиць понад мільйон рядків.

## Нова колонка NOT NULL

1. Ревізія A: `add_column(..., nullable=True)`.
2. Заповнення пачками (окремий скрипт або фонова задача), а не одним `UPDATE`.
3. Ревізія B: `alter_column(..., nullable=False)` — після того як порожніх значень не лишилось.

## Індекс

```python
with op.get_context().autocommit_block():
    op.create_index(
        "ix_orders_external_ref", "orders", ["external_ref"], postgresql_concurrently=True
    )
```

`downgrade()` — `drop_index(..., postgresql_concurrently=True)` у такому ж блоці.

## Зовнішній ключ

1. Ревізія A: `create_foreign_key(..., postgresql_not_valid=True)` — без скану таблиці.
2. Ревізія B: `op.execute("ALTER TABLE … VALIDATE CONSTRAINT …")` — бере слабший лок.

## Перейменування колонки

Не перейменовувати на живій таблиці. Додати нову, писати в обидві, перевести читання, видалити стару — чотири релізи.
