FROM alpine:3.18

RUN apk add --no-cache python3 py3-pip curl

WORKDIR /app

RUN adduser -D appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY gitlab_util.py .
COPY app.py .

RUN chown -R appuser:appuser /app

ENV PYTHONUNBUFFERED=1

USER appuser

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

EXPOSE 5000

CMD ["python3", "app.py"]