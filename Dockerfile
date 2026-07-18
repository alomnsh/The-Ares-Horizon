# Use an official, stable Debian slim layer with full system package management
FROM debian:bookworm-slim

# Force non-interactive package installations to prevent build hangs
ENV DEBIAN_FRONTEND=noninteractive

# 1. Install Linux core UI stacks, virtual displays, audio utilities, imaging support, and Nginx web server
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-tk \
    python3-pygame \
    python3-pil.imagetk \
    procps \
    libjpeg-dev \
    zlib1g-dev \
    xvfb \
    x11vnc \
    websockify \
    novnc \
    fluxbox \
    alsa-utils \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# 2. FIXED PROXY LOCATION: Notice the trailing slashes which fix the invalid header packet drops
RUN echo 'server {\n\
    listen 10000;\n\
    root /usr/share/novnc;\n\
    index vnc.html;\n\
\n\
    location / {\n\
        try_files $uri $uri/ =404;\n\
    }\n\
\n\
    location /websockify/ {\n\
        proxy_pass http://127.0.0;\n\
        proxy_http_version 1.1;\n\
        proxy_set_header Upgrade $http_upgrade;\n\
        proxy_set_header Connection "Upgrade";\n\
        proxy_set_header Host $host;\n\
        proxy_read_timeout 61s;\n\
        proxy_buffering off;\n\
    }\n\
}' > /etc/nginx/sites-available/default

# 3. Create a dedicated user for cloud execution
RUN useradd -m -u 1000 user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    DISPLAY=:1

WORKDIR /home/user/app

# 4. Import project assets and fix folder execution permissions
COPY --chown=user:user . /home/user/app

# Install Python requirements cleanly to the local user space
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# 5. Create the automated system runtime boot sequence script
RUN echo '#!/bin/bash\n\
# Start Nginx web router engine via root authority prior to dropping down privileges\n\
nginx -g "daemon on;"\n\
\n\
# Drop root permissions and switch safely to the local container user context\n\
su user -c "\n\
# Initialize a virtual hidden monitor canvas\n\
Xvfb :1 -screen 0 1024x768x24 &\n\
sleep 1\n\
\n\
# Boot the window manager\n\
fluxbox &\n\
sleep 1\n\
\n\
# Map the local window buffer to a secure background VNC bridge port\n\
x11vnc -forever -shared -rfbport 5900 -nopw -display :1 &\n\
sleep 1\n\
\n\
# Route websocket channels right into Nginx via localized secure port 5901\n\
websockify 5901 localhost:5900 &\n\
sleep 1\n\
\n\
# Run your core game file directly\n\
python3 \"The Ares Horizon.py\"\n\
"\n\
' > /start.sh && chmod +x /start.sh

# Open Render network interface channels
EXPOSE 10000

# Kick off the system runtime boot script on app launch
CMD ["/start.sh"]
