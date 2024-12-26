# Dockerfile
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install poetry
RUN pip install poetry

# Set the working directory
WORKDIR /app

# Install dependencies
COPY poetry.lock pyproject.toml .
RUN poetry install

# Copy the application code
COPY . .

# Command to run the application
CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
