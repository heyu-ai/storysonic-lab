FROM python:3.13-slim-bookworm
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HF_HOME=/work/data/huggingface
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml requirements-cpu.lock ./
COPY storysonic/*.py ./storysonic/
COPY scripts/install-gws.py /tmp/install-gws.py
RUN pip install --require-hashes -r requirements-cpu.lock \
    && pip install --no-deps . \
    && python /tmp/install-gws.py \
    && rm /tmp/install-gws.py \
    && useradd --create-home --uid 1000 worker \
    && mkdir -p /work/content /work/data /work/outputs \
    && chown -R worker:worker /work
WORKDIR /work
USER worker
ENTRYPOINT ["storysonic"]
CMD ["--help"]
