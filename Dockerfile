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

EXPOSE 5050
ENV NAME Archivist
CMD ["gunicorn", "-w", "1", "--threads", "8", "-b", "0.0.0.0:5050", "main:app"]