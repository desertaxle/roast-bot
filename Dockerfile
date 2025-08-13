FROM prefecthq/prefect:3-latest

WORKDIR /app
SHELL ["/bin/bash", "--login", "-c"]

# install necessary packages
RUN apt-get update && apt-get install -y curl gpg unzip

# add gh GPG key
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg;

# add gh repository
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null;

# install gh
RUN apt-get update && apt-get install -y gh;

# download and install nvm:
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash

# install node
RUN nvm install 22 && nvm use 22

# verify the node and npm versions:
RUN node -v
RUN npm -v

# install claude-code
RUN npm install -g @anthropic-ai/claude-code

# verify the claude-code version:
RUN claude --version

# install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_SYSTEM_PYTHON=1
ENV UV_COMPILE_BYTECODE=1

# install dependencies
COPY pyproject.toml .
RUN uv pip install -r pyproject.toml

# copy code
COPY main.py .