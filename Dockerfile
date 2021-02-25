FROM python:3.8

RUN mkdir /gme_shorts

COPY /gme_shorts /gme_shorts/gme_shorts
COPY pyproject.toml /gme_shorts
COPY wsgi.py /gme_shorts
COPY gunicorn.conf.py /gme_shorts

WORKDIR /gme_shorts
ENV PYTHONPATH=${PYTHONPATH}:${PWD}

RUN pip3 install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

EXPOSE 5000
