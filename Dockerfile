# Build web UI — `ui/dist` is gitignored, so the image must produce it or Flask serves stale `ui_dist/`.
FROM node:22-bookworm-slim AS ui
WORKDIR /ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci
COPY ui/ ./
RUN npm run build

FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04
WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3.10 python3-pip git openssh-client rsync ffmpeg espeak-ng \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 \
    && python -m pip install --upgrade pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2 --index-url https://download.pytorch.org/whl/cu121
RUN pip install --no-cache-dir ctranslate2==4.3.1 --extra-index-url https://pip.nvidia.com --extra-index-url https://download.pytorch.org/whl/cu121
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m nltk.downloader punkt punkt_tab

COPY . .
COPY --from=ui /ui/dist ./ui/dist

EXPOSE 5050
EXPOSE 5051
ENV NAME Archivist
CMD ["gunicorn", "-w", "1", "--threads", "64", "--timeout", "3600", "-b", "0.0.0.0:5050", "main:app"]
