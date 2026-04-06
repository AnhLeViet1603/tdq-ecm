FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-traditional \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY services/ai/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ /app/shared/
COPY services/ai/ .

COPY services/ai/auto_init.sh .
RUN chmod +x auto_init.sh entrypoint.sh

RUN chmod +x entrypoint.sh

EXPOSE 8010

ENTRYPOINT ["./entrypoint.sh"]
