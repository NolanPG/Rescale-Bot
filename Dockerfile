FROM python:3.9-buster

ENV PYTHONDONTWRITEBYTECODE=1

ENV PYTHONBUFFERED=1

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt
RUN apt update

WORKDIR /app
COPY . /app

CMD ["bash", "run.sh"]
