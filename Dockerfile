FROM python:3.11-slim-bullseye

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

ENV POETRY_VERSION=1.8.3
ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_NO_INTERACTION=1
ENV POETRY_CACHE_DIR=/tmp/poetry-cache
ENV PIP_NO_CACHE_DIR=1

COPY pyproject.toml ./
RUN pip install --upgrade pip \
    && pip install "poetry==${POETRY_VERSION}" \
    && poetry install --only main --no-root \
    && pip uninstall -y poetry \
    && rm -rf "${POETRY_CACHE_DIR}" /root/.cache/pip /root/.cache/pypoetry

COPY . .

ENV PYTHONPATH="/app"

EXPOSE 8001
