# Dockerfile
FROM python:3.10-slim
ENV PYTHONUNBUFFERED True
ENV PORT 8080
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
# Use Gunicorn to run the 'app' object inside the 'app' package
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "run:app"]