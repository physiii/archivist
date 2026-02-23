# Build UI
FROM node:20-alpine AS ui-builder
WORKDIR /ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci
COPY ui/ ./
RUN npm run build

# API runtime
FROM python:3.10-slim
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends rsync \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m nltk.downloader punkt punkt_tab

COPY . .
COPY --from=ui-builder /ui/dist ./ui_dist

EXPOSE 5050
ENV NAME Vectorstore
CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:5050", "main:app"]