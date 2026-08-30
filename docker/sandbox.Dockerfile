FROM python:3.11-slim
WORKDIR /workspace
RUN pip install --no-cache-dir pytest
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
