FROM prefecthq/prefect:3-latest

WORKDIR /app

# install necessary packages
RUN apt-get update && apt-get install -y \
curl \
gpg

# add gh GPG key
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg;

# add gh repository
RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null;

# install gh
RUN apt-get update && apt-get install -y gh;

# download and install fnm:
curl -o- https://fnm.vercel.app/install | bash

# download and install Node.js:
fnm install 22

# verify the Node.js version:
node -v

# verify npm version:
npm -v
    

# install claude-code
RUN npm install -g @anthropic-ai/claude-code

# install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# install dependencies
COPY pyproject.toml .
RUN uv sync --no-dev --compile-bytecode
ENV PATH="/app/.venv/bin:$PATH"

# copy code
COPY main.py .