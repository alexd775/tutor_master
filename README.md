# AI Tutor Platform

A state-of-the-art AI tutoring platform that combines the power of large language models with the joy of learning.

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL
- Redis
- A sense of humor

### Setup
1. Clone the repository
```
bash
git clone <repository-url>
cd app
```

2. Install dependencies with Poetry
```
poetry install
```

3. Copy the .env.example file and create a new .env file
```
cp .env.example .env
```

Edit the .env file with your own values.

4. Initialize the database
```
poetry run alembic upgrade head
```

5. Create a superuser (admin)
```
poetry run python -m app.scripts.create_superuser
# Or use the management script
poetry run python -m app.scripts.manage createsuperuser
```

6. Management commands
```
# Create superuser
poetry run python -m app.scripts.manage createsuperuser

# Activate/deactivate user
poetry run python -m app.scripts.manage manage-user user@example.com --active
poetry run python -m app.scripts.manage manage-user user@example.com --inactive

# Clean up inactive sessions older than 30 days
poetry run python -m app.scripts.manage cleanup-inactive 30

# Export topics to JSON
poetry run python -m app.scripts.manage export-topics topics.json

# Import topics (skip existing)
poetry run python -m app.scripts.manage import-topics topics.json

# Import and update existing topics
poetry run python -m app.scripts.manage import-topics topics.json --update

# Show system statistics
poetry run python -m app.scripts.manage show_stats
```

7. Run the development server
```
poetry run uvicorn app.main:app --reload
```

## Project Structure

app/
├── api/ # API endpoints (where the magic happens)
├── core/ # Core configurations (the boring but important stuff)
├── models/ # Database models (because data needs structure)
├── schemas/ # Pydantic models (type hints FTW)
├── services/ # Business logic (the real spaghetti code goes here)
└── utils/ # Utility functions (for when you're feeling DRY)

## 🧪 Testing

To run the tests, use the following command:
```
poetry run pytest
```

## Documentation

API documentation available at `/docs` when running the server.
http://localhost:8000/docs 



