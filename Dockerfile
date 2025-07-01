FROM ghcr.io/astral-sh/uv:python3.11-alpine
LABEL name="Casaflix" \
      description="Decentralized shared streaming." \
      url="https://github.com/putupau/comet"

WORKDIR /app

ARG DATABASE_PATH

COPY pyproject.toml .

RUN uv sync

COPY . .

ENTRYPOINT ["uv", "run", "python", "-m", "comet.main"]
