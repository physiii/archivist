# Build web UI — `ui/dist` is gitignored, so the image must produce it or Flask serves stale `ui_dist/`.
FROM node:22-bookworm-slim AS ui
WORKDIR /ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci
COPY ui/ ./
RUN npm run build

FROM python:3.10-slim
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends openssh-client rsync \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m nltk.downloader punkt punkt_tab

COPY . .
COPY --from=ui /ui/dist ./ui/dist

EXPOSE 5050
ENV NAME Archivist
CMD ["gunicorn", "-w", "1", "--threads", "8", "-b", "0.0.0.0:5050", "main:app"]
