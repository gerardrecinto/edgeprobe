FROM python:3.15-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

ENTRYPOINT ["edgeprobe"]
CMD ["--help"]

