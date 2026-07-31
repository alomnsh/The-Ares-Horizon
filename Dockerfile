FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-tk \
    python3-pil.imagetk \
    xvfb \
    x11vnc \
    novnc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages
COPY . .

EXPOSE 8080

CMD Xvfb :99 -screen 0 1280x720x16 & \
    sleep 1 && \
    export DISPLAY=:99 && \
    export SDL_AUDIODRIVER=dummy && \
    python3 "The Ares Horizon.py" & \
    x11vnc -forever -shared -display :99 -nopw -listen localhost -bg -sync && \
    python3 -m websockify 8080 localhost:5900 --web /usr/share/novnc --heartbeat 10
