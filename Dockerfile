# ******* running from the sheel *********
# cd ~
# rm -rf rebalancing-trading-bot
# git clone -b dockerize_app --single-branch https://github.com/harikrishna2005/rebalancing-trading-bot.git
# cd rebalancing-trading-bot
# docker compose build --no-cache
# docker compose up -d
# *********** NOT REQUIRED --- docker compose up -d --build --no-cache
# docker compose down --rmi local
# docker image prune -f
#
#
# ===
# docker compose build --no-cache
# docker compose up -d

# Add these at the very top
# Global ARG available before any FROM
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Use the platform-specific base image
FROM --platform=$TARGETPLATFORM python:3.12-slim-bookworm AS builder

# --- Stage 1: Build ---
# FROM python:3.12-slim-bookworm AS builder
# Re-declare ARG inside the stage to use it here
ARG TARGETPLATFORM


ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1

RUN apt-get update && apt-get install -y git build-essential python3-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app
RUN pip install poetry

# Copy everything first (including src) so Poetry can "install" your local package
COPY . .

# Now, when this runs, it installs dependencies AND your rebalancing_bot
RUN poetry install --all-extras

# --- Stage 2: Runtime ---
# FROM python:3.12-slim-bookworm AS runtime
FROM --platform=$TARGETPLATFORM python:3.12-slim-bookworm AS runtime
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Copy the entire virtual env and the source
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src ./src
# COPY config.json ./

# This will now work because 'rebalancing_bot' is installed in the .venv
# ENTRYPOINT ["python", "-m", "rebalancing_bot"]
# ENTRYPOINT ["run-bot"]