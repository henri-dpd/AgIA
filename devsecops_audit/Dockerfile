FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY devsecops_auditor.py ./
COPY doc ./doc

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

ENTRYPOINT ["agia-devsecops-audit"]
CMD ["--help"]
