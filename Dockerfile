FROM python:3.11-slim

RUN apt-get update && apt-get install -y chromium chromium-driver curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tests

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["pytest", "-v", "--junitxml=reports/results.xml"]