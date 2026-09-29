FROM python:3.12-slim
RUN pip install --no-cache-dir "pyjwt[crypto]==2.15.1" "cryptography==50.0.1"
WORKDIR /app
COPY . /app
ENV PYTHONUNBUFFERED=1
