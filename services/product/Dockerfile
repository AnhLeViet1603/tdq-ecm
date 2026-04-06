FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY services/product/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ /app/shared/
COPY services/product/ .

COPY services/product/auto_init.sh .
RUN chmod +x auto_init.sh entrypoint.sh

RUN chmod +x entrypoint.sh

EXPOSE 8002

ENTRYPOINT ["./entrypoint.sh"]
