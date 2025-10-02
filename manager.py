#!/usr/bin/env python3
import os, sys, time, subprocess
from utils import *

ensure_dirs()

ACTIVE_STREAMS_FILE = os.path.join(os.getcwd(), "active_streams.txt")

def save_active_stream(key):
    keys = []
    if os.path.exists(ACTIVE_STREAMS_FILE):
        keys = [line.strip() for line in open(ACTIVE_STREAMS_FILE)]
    if key not in keys:
        with open(ACTIVE_STREAMS_FILE, "a") as f:
            f.write(key + "\n")

def remove_active_stream(key):
    if not os.path.exists(ACTIVE_STREAMS_FILE):
        return
    keys = [line.strip() for line in open(ACTIVE_STREAMS_FILE)]
    keys = [k for k in keys if k != key]
    with open(ACTIVE_STREAMS_FILE, "w") as f:
        for k in keys:
            f.write(k + "\n")

def get_active_streams():
    if not os.path.exists(ACTIVE_STREAMS_FILE):
        return []
    return [line.strip() for line in open(ACTIVE_STREAMS_FILE)]


def start_stream():
    key = input("Введіть код трансляції (назва папки): ").strip()
    if not key:
        print("Скасовано.")
        return
    folder = stream_path(key)
    os.makedirs(folder, exist_ok=True)

    pid = read_pid(key)
    if pid:
        print(f"Такий стрім вже йде (pid {pid}).")
        return

    files = list_video_files(folder)
    if files:
        print(f"Знайдено {len(files)} відео у папці {folder}.")
        print("1) Підтвердити запуск")
        print("2) Довантажити/видалити відео")
        print("3) Повернутись у головне меню")
        choice = input("> ").strip()
        if choice == "2":
            manage_files_menu(key)
            files = list_video_files(folder)
            if files:
                print("Є принаймні один файл — запускаю трансляцію…")
                launch_worker(key)
        elif choice == "1":
            launch_worker(key)
        else:
            return
    else:
        print(f"У папці {folder} немає відео. Створено/перевірено папку.")
        print("Завантажте відео у цю папку, приклад:")
        print(f"scp /шлях/до/файлів/*.mp4 user@SERVER:{folder}/")
        confirm = input("Запустити очікування та старт при появі першого файла? (y/N): ").strip().lower()
        if confirm == "y":
            launch_worker(key)

def stop_stream():
    key = input("Введіть код трансляції: ").strip()
    pid = read_pid(key)
    if not pid:
        print("Стрім не знайдено або вже зупинено.")
        return
    print(f"Знайдено процес pid={pid}.")
    print("1) Підтвердити зупинку")
    print("2) Відміна")
    choice = input("> ").strip()
    if choice == "1":
        try:
            os.kill(pid, 15)
            time.sleep(1)
        except Exception as e:
            print("Помилка сигналу:", e)
        if not read_pid(key):
            print("Зупинено.")
        else:
            print("Не вдалося зупинити миттєво. Спробуйте ще раз або використайте: kill", pid)

def list_streams():
    active = []
    for fn in os.listdir(RUN_DIR):
        if not fn.endswith(".pid"): continue
        key = fn[:-4]
        pid = read_pid(key)
        if pid:
            active.append((key, pid))
        else:
            clear_pid(key)
    if not active:
        print("Активних трансляцій немає.")
    else:
        print("Активні трансляції:")
        for key, pid in active:
            print(f"- {key} (pid {pid})")

def manage_files_menu(key: str):
    folder = stream_path(key)
    while True:
        print(f"\nПапка: {folder}")
        files = list_video_files(folder)
        if files:
            print("Файли:")
            for i,f in enumerate(files,1):
                print(f"  {i}. {f}")
        else:
            print("Файлів поки немає.")
        print("\n1) Догрузити (підказка команд завантаження)")
        print("2) Видалити (імена через кому)")
        print("3) Повернутись у головне меню")
        choice = input("> ").strip()
        if choice == "1":
            print("\nПриклад завантаження з вашого ПК:")
            print(f"scp /path/video1.mp4 /path/video2.mkv user@SERVER:{folder}/")
        elif choice == "2":
            names = input("Введіть імена для видалення: ").strip()
            if not names: continue
            for name in [x.strip() for x in names.split(",") if x.strip()]:
                p = os.path.join(folder, name)
                try:
                    os.remove(p)
                    print("Видалено:", name)
                except FileNotFoundError:
                    print("Не знайдено:", name)
                except Exception as e:
                    print("Помилка:", e)
        else:
            break

def launch_worker(key: str):
    if read_pid(key):
        print("Такий стрім вже йде.")
        return
    cmd = [sys.executable, os.path.join(os.getcwd(),"streamer.py"), "--key", key]
    logf = logfile_path(key)
    with open(logf,"ab") as lf:
        lf.write(b"\n=== MANAGER START ===\n")
    subprocess.Popen(cmd, stdout=open(os.devnull,"wb"), stderr=open(logf,"ab"))
    time.sleep(0.5)
    pid = read_pid(key)
    if pid:
        print(f"Стрім {key} запущено (pid {pid}).")
    else:
        print("Не вдалось визначити запуск. Перевірте логи:", logf)

def calc_resource():
    cap = estimate_capacity()
    print(f"Оціночна кількість стрімів у режимі copy (без перекодування): ~ {cap}")

def main_menu():
    while True:
        print("\n==== YouTube Streamer (CLI) ====")
        print("1) Запустити стрім")
        print("2) Зупинити стрім")
        print("3) Перевірити скільки трансляцій запущено")
        print("4) Розрахувати ресурс")
        print("5) Вийти зі скрипта")
        choice = input("> ").strip()
        if choice == "1":
            start_stream()
        elif choice == "2":
            stop_stream()
        elif choice == "3":
            list_streams()
        elif choice == "4":
            calc_resource()
        elif choice == "5":
            print("Bye.")
            break

if __name__ == "__main__":
    main_menu()
