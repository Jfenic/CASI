FROM python:3.11-slim

RUN groupadd --system casi \
    && useradd --system --gid casi --create-home --home-dir /home/casi --shell /usr/sbin/nologin casi

WORKDIR /workspace
RUN pip install --no-cache-dir pytest

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER casi

ENTRYPOINT ["/entrypoint.sh"]
