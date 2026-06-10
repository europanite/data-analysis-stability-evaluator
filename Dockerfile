FROM python:3.11-slim

WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY tests ./tests
COPY examples ./examples
COPY docs ./docs

RUN python -m pip install --upgrade pip \
    && python -m pip install -e ".[dev,plots]"

CMD ["pytest"]
