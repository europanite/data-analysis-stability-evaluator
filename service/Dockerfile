FROM python:3.12-slim

WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY pyproject.toml README.md LICENSE ./
COPY service/src ./service/src
COPY service/tests ./service/tests
COPY service/examples ./service/examples

RUN python -m pip install --upgrade pip \
    && python -m pip install -e ".[dev]"

CMD ["pytest"]
