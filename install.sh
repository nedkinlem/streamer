#!/usr/bin/env bash
set -e

# === Папка проєкту ===
APP_DIR="/root/hetzner-yt-streamer-full"

echo "[1/5] Оновлення системи..."
apt update && apt install -y python3 python3-venv python3-pip ffmpeg git

echo "[2/5] Клонування або оновлення репозиторію..."
if [ ! -d "$APP_DIR" ]; then
    git clone https://github.com/nedkinlem/streamer.git "$APP_DIR"
else
    cd "$APP_DIR"
    git pull
fi

cd "$APP_DIR"

echo "[3/5] Створення Python venv..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install psutil

echo "[4/5] Створення запускного файлу ytstreamer..."
cat > ytstreamer <<'EOF'
#!/usr/bin/env bash
cd /root/hetzner-yt-streamer-full
source .venv/bin/activate
exec python manager.py "$@"
EOF

chmod +x ytstreamer

echo "[5/5] Встановлення завершене!"
echo "Запускати можна так:"
echo "  cd $APP_DIR && ./ytstreamer"
