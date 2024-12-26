# Alembic

## Initialize alembic

```
poetry run alembic init alembic
```

## Create initial migration

```
poetry run alembic revision --autogenerate -m "Initial migration"
```

## Run the migration
```
poetry run alembic upgrade head
```

## Downgrade the migration
```
poetry run alembic downgrade
```

## Generate a new migration
```
poetry run alembic revision --autogenerate -m "New migration"
```

