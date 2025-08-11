FROM prefecthq/prefect:3-latest

# install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# install curl
RUN apt update && apt install curl -y

# install claude-code
RUN curl -fsSL https://claude.ai/install.sh | bash

# install dependencies
COPY pyproject.toml .
RUN uv sync --no-dev

# copy code
COPY main.py .