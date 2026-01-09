FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set work directory
WORKDIR /app

# Copy pyproject.toml
COPY pyproject.toml .

# Install dependencies
RUN uv pip install --system -e .

# Default command
CMD ["mcp-server-ladybug", "--db-path", ":memory:"]