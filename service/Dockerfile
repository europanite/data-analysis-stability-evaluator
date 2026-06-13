FROM python:3.12-slim

WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY pyproject.toml ./
COPY src ./src
COPY tests ./tests
COPY examples ./examples

RUN python -m pip install --upgrade pip \
    && python -m pip install -e ".[dev,plots]"

CMD ["pytest"]
