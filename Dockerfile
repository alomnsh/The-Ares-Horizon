# Use an official, stable Debian slim layer with full system package management
FROM debian:bookworm-slim

# Force non-interactive package installations to prevent build hangs
ENV DEBIAN_FRONTEND=noninteractive

# 1. Install Linux core UI stacks, virtual displays, audio utilities, imaging support, TigerVNC, and noVNC
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
    tigervnc-standalone-server \
    tigervnc-tools \
    websockify \
    novnc \
    fluxbox \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# 2. Tighten security profiles via custom non-root runtime environments
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    DISPLAY=:1

WORKDIR /home/user/app

# 3. Import project assets and fix folder execution permissions
COPY --chown=user:user . /home/user/app

# Sync local dependencies directly to user environments
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# 4. Create a clean system boot sequence layout script
RUN echo '#!/bin/bash\n\
# Safe removal profiles ensure dirty locks do not block startup\n\
rm -rf /tmp/.X11-unix/X1 /tmp/.X1-lock\n\
\n\
# FIXED: Added required safety override flags to force TigerVNC to cooperate on public cloud instances\n\
vncserver :1 -geometry 1024x768 -depth 24 -SecurityTypes None -localhost no --I-KNOW-THIS-IS-INSECURE &\n\
sleep 3\n\
\n\
# Boot your basic window workspace framework manager profiles\n\
DISPLAY=:1 fluxbox &\n\
sleep 1\n\
\n\
# Launch core game scripts directly in the target virtual frame\n\
DISPLAY=:1 python3 "The Ares Horizon.py" &\n\
sleep 1\n\
\n\
# Use the absolute, built-in system paths to launch the Render-optimized web client proxy\n\
/usr/share/novnc/utils/novnc_proxy --vnc localhost:5901 --listen 10000\n\
' > /home/user/app/start.sh && chmod +x /home/user/app/start.sh

# Open Render network interface channels
EXPOSE 10000

# Kick off the system runtime boot script on app launch
CMD ["/home/user/app/start.sh"]
