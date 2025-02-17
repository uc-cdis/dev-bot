FROM quay.io/cdis/python-nginx:master

ENV appname=devbot

ENV DEBIAN_FRONTEND=noninteractive

RUN adduser -D -g '' devbotuser

RUN mkdir -p /opt/ctds/devbot \
    && chown devbotuser /opt/ctds/devbot

COPY . /opt/ctds/devbot
WORKDIR /opt/ctds/devbot

ENV CRYPTOGRAPHY_ALLOW_OPENSSL_102=true
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev openssl-dev gcc g++ curl

USER devbotuser

EXPOSE 8080

RUN pip install --upgrade pip --user

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python

# cache so that poetry install will run if these files change
COPY poetry.lock pyproject.toml /opt/ctds/devbot/

# Install dev-bot and dependencies via poetry
RUN source $HOME/.poetry/env \
    && poetry config virtualenvs.create false \
    && poetry install -vv --no-dev --no-interaction \
    && poetry show -v

WORKDIR /opt/ctds/devbot/devbot

ENTRYPOINT source $HOME/.poetry/env && poetry run python3.6 devbot.py
