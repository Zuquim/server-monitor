FROM python:3.7-alpine
MAINTAINER User <user@domain>
WORKDIR /app
COPY server-monitor.py ./
ENV PYTHONUNBUFFERED=0
CMD ["sh", "-c", "PYTHONUNBUFFERED=0 eval python3 /app/server-monitor.py $OPTIONS"]
