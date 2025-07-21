FROM python:3.13-slim

# Install ffmpeg
RUN apt-get update && apt-get install -y git curl ripgrep jq && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install nvm, Node.js, and npm in one RUN to preserve environment
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash \
    && export NVM_DIR="$HOME/.nvm" \
    && [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" \
    && nvm install 22 \
    && nvm use 22 \
    && nvm alias default 22 \
    && ln -sf $NVM_DIR/versions/node/v22.*/bin/node /usr/local/bin/node \
    && ln -sf $NVM_DIR/versions/node/v22.*/bin/npm /usr/local/bin/npm \
    && ln -sf $NVM_DIR/versions/node/v22.*/bin/npx /usr/local/bin/npx \
    && node -v \
    && npm -v \
    && npx -v

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