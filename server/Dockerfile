FROM python:3.13-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y git nodejs npm && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN npm install -g npx

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ADD . /app

# Sync the project into a new environment, asserting the lockfile is up to date
WORKDIR /app
RUN uv sync --locked

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


# Command to run the application
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]