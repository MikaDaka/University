# syntax=docker/dockerfile:1
FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    xvfb \
    x11vnc \
    fluxbox \
    websockify \
    novnc \
    python3-tk \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY client.py server_base.py ./

# Создаём скрипт запуска Xvfb + noVNC + клиент
RUN printf '#!/bin/sh\n' > /start.sh \
 && printf 'Xvfb :1 -screen 0 1280x720x24 &\n' >> /start.sh \
 && printf 'export DISPLAY=:1\n' >> /start.sh \
 && printf 'fluxbox &\n' >> /start.sh \
 && printf 'x11vnc -display :1 -forever -nopw -shared &\n' >> /start.sh \
 && printf 'websockify --web=/usr/share/novnc/ 6080 5900 &\n' >> /start.sh \
 && printf 'sleep 1\n' >> /start.sh \
 && printf 'python client.py\n' >> /start.sh \
 && chmod +x /start.sh

EXPOSE 6080

CMD ["/start.sh"]

