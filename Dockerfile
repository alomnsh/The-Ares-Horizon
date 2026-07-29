FROM debian:bookworm-slim

# Install system dependencies for GUI, Audio, and noVNC streaming
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-tk \
    xvfb \
    x11vnc \
    novnc \
    openbox \
    alsa-utils \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# Copy the rest of the game assets and code
COPY . .

# Render expects port 8080 exposed for web traffic
EXPOSE 8080

# 1. Start virtual display
# 2. Run window manager so fullscreen works
# 3. Suppress audio card requirements
# 4. Use the correct absolute Debian binary path for novnc_proxy
CMD Xvfb :99 -screen 0 1024x768x16 & \
    sleep 1 && \
    export DISPLAY=:99 && \
    export SDL_AUDIODRIVER=dummy && \
    openbox & \
    python3 "The Ares Horizon.py" & \
    x11vnc -forever -shared -display :99 -nopw -listen localhost & \
    /usr/libexec/novnc/novnc_proxy --vnc localhost:5900 --listen 8080
