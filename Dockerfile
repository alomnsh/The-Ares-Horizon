# Use an official, stable Debian slim layer with full system package management
FROM debian:bookworm-slim

# Force non-interactive package installations to prevent build hangs
ENV DEBIAN_FRONTEND=noninteractive

# 1. Install Linux core UI stacks, virtual displays, audio utilities, imaging support, and web proxies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-tk \
    python3-pygame \
    libjpeg-dev \
    zlib1g-dev \
    xvfb \
    x11vnc \
    websockify \
    novnc \
    fluxbox \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# 2. Strict Security: Create a dedicated non-root user for Hugging Face compatibility
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    DISPLAY=:1

WORKDIR /home/user/app

# 3. Import project assets and fix folder execution permissions
COPY --chown=user:user . /home/user/app

# Install Python requirements cleanly to the local user space
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# 4. Create the automated system runtime boot sequence script
RUN echo '#!/bin/bash\n\
# Initialize a virtual hidden monitor canvas matching desktop dimensions\n\
Xvfb :1 -screen 0 1024x768x24 &\n\
sleep 1\n\
\n\
# Boot a simple, ultra-lightweight Linux window manager\n\
fluxbox &\n\
sleep 1\n\
\n\
# Map the local window buffer to a secure background VNC bridge port\n\
x11vnc -forever -shared -rfbport 5900 -nopw -display :1 &\n\
sleep 1\n\
\n\
# Launch websockify to stream the VNC output straight into HTML5 port 7860\n\
/usr/share/novnc/utils/novnc_proxy --vnc localhost:5900 --listen 7860 &\n\
sleep 1\n\
\n\
# Run your core game file directly in the cloud container\n\
python3 "The Ares Horizon.py"\n\
' > /home/user/app/start.sh && chmod +x /home/user/app/start.sh

# Open Hugging Face Space network interface channels
EXPOSE 7860

# Kick off the system runtime boot script on app launch
CMD ["/home/user/app/start.sh"]
