FROM node:22-bookworm AS frontend

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


# Build the YouTube PO-token provider
FROM node:22-bookworm-slim AS pot-provider

RUN apt-get update && apt-get install -y \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN git clone \
    --depth 1 \
    --branch 2.0.0 \
    https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git

WORKDIR /opt/bgutil-ytdlp-pot-provider/server

RUN npm ci
RUN npx tsc
RUN npm prune --omit=dev


# Main ClipForge container
FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libstdc++6 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*


# Node 22 runtime for yt-dlp + PO token provider
COPY --from=pot-provider \
    /usr/local/bin/node \
    /usr/local/bin/node

# PO token provider server
COPY --from=pot-provider \
    /opt/bgutil-ytdlp-pot-provider/server \
    /opt/bgutil-provider


COPY backend/requirements.txt /app/backend/requirements.txt

RUN pip install \
    --no-cache-dir \
    -r /app/backend/requirements.txt


COPY backend /app/backend

COPY --from=frontend \
    /app/frontend/dist \
    /app/frontend/dist


RUN mkdir -p \
    /app/data/uploads \
    /app/data/clips \
    /app/data/exports


WORKDIR /app/backend


CMD ["sh", "-c", "node /opt/bgutil-provider/build/main.js --host 127.0.0.1 --port 4416 & sleep 1 && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]