FROM python:3.13-alpine

WORKDIR /app

COPY requirements.txt /app

RUN pip install -r requirements.txt

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

COPY . /app

RUN pip install flask-migrate


ENTRYPOINT ["/app/entrypoint.sh"]


