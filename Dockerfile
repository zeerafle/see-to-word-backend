# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.12-slim

# install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container.
COPY . /app

# install the application dependencies
WORKDIR /app
RUN uv sync --frozen --no-cache

# Expose the port that the app runs on
EXPOSE 8000

# Set the environment variable
ENV ENV=production

# Run the application
CMD ["/app/.venv/bin/fastapi", "run", "main.py", "--port", "8000", "--host", "0.0.0.0"]
