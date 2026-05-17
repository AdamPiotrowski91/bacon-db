FROM python:3.14-alpine3.23

WORKDIR /app

# Copy your library and project files
COPY src .

# Install the library
RUN pip install --no-cache-dir tox python-dotenv .
