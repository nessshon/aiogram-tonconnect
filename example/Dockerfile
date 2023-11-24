FROM python:3.10-slim-buster

WORKDIR /usr/src/bot

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip &&  \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "cd /usr/src/bot && python -m bot"]