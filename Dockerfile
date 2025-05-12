FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    gcc \
    libc-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*


RUN pip install --no-cache-dir poetry

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-root


COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010", "--reload"]