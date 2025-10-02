#!/usr/bin/env bash
set -e
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
mkdir -p streams run logs
echo "Установка завершена"
