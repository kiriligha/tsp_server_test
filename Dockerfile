FROM python:3.12-slim

WORKDIR /app

COPY server/server.py .

EXPOSE 6379

CMD ["python", "server.py"]