FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    fonts-liberation \
    libcurl3-gnutls \
    libgbm1 \
    libasound2 \
    libvulkan1 \
    xdg-utils \
    libx11-xcb1 \
    libxss1 \
    libnss3 \
    libatk-bridge2.0-0 \
    libcups2 \
    libatk1.0-0 \
    libxcomposite1 \
    libxrandr2 \
    libgconf-2-4 \
    --no-install-recommends

RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb

RUN wget https://storage.googleapis.com/chrome-for-testing-public/131.0.6778.108/linux64/chromedriver-linux64.zip \
    && apt-get install -y unzip \
    && unzip chromedriver-linux64.zip \
    && mv chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && rm -rf chromedriver-linux64.zip chromedriver-linux64

RUN apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app
WORKDIR /app

EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
