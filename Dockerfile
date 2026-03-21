FROM python:3.11.9-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libssl-dev libffi-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip setuptools wheel

RUN pip install --no-cache-dir --only-binary=:all: \
    pydantic-core==2.18.2 \
    pydantic==2.7.1

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install --no-cache-dir uvloop httptools

COPY . .

RUN mkdir -p uploads static/css static/js templates

EXPOSE 10000

HEALTHCHECK CMD curl --fail http://localhost:$PORT/health || exit 1

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2 --loop uvloop --http httptools"]