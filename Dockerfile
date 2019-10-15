FROM python:3.7-alpine

WORKDIR /app/server
COPY . /app/server

RUN \
    apk add --no-cache postgresql-libs && \
    apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
    python3 -m pip install -r requirements.txt --no-cache-dir && \
    apk --purge del .build-deps

RUN pip install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 5000

RUN adduser -D myuser
USER myuser

ENV FLASK_APP api
ENV FLASK_ENV development
CMD flask run --host=0.0.0.0
