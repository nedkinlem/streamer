#!/usr/bin/env python3
import os, sys, time, random, argparse, signal
from utils import *

RUNNING = True
def handle_sigterm(signum, frame):
    global RUNNING
    RUNNING = False
signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True)
    parser.add_argument("--url", default=DEFAULT_RTMP_URL)
    args = parser.parse_args()

    ensure_dirs()
    key, url = args.key, args.url
    folder = stream_path(key)
    os.makedirs(folder, exist_ok=True)

    write_pid(key, os.getpid())
    try:
        while RUNNING:
            files = list_video_files(folder)
            if not files:
                time.sleep(2)
                continue
            random.shuffle(files)
            for f in files:
                if not RUNNING: break
                path = os.path.join(folder, f)
                if not is_youtube_compatible(path):
                    path = reencode_to_youtube(path) or path
                stream_video(path, url, key)
    finally:
        clear_pid(key)
    return 0

if __name__ == "__main__":
    sys.exit(main())
