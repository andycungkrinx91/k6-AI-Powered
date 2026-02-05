FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && \
    apt-get install -y curl gnupg nodejs npm && \
    rm -rf /var/lib/apt/lists/*

# Install k6
RUN curl -L https://github.com/grafana/k6/releases/download/v1.5.0/k6-v1.5.0-linux-amd64.tar.gz \
    | tar -xz && \
    mv k6-v1.5.0-linux-amd64/k6 /usr/bin/k6 && \
    chmod +x /usr/bin/k6

# Install python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser (Chromium) with system deps
RUN python -m playwright install --with-deps chromium

# Install Lighthouse (node)
RUN npm install -g lighthouse

# Copy app
COPY app ./app
COPY assets ./assets


CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
