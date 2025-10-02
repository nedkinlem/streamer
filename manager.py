#!/usr/bin/env python3
import os, sys, time, subprocess
from utils import *

ensure_dirs()

def main_menu():
    while True:
        print("\n1) Запустити стрім")
        print("2) Вийти")
        ch = input("> ")
        if ch == "1":
            key = input("Введіть код трансляції: ").strip()
            folder = stream_path(key)
            os.makedirs(folder, exist_ok=True)
            cmd = [sys.executable, "streamer.py", "--key", key]
            subprocess.Popen(cmd)
            print("Стрім запущено")
        elif ch == "2":
            break

if __name__ == "__main__":
    main_menu()
