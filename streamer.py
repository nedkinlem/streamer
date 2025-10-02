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
    parser.add_argument("--key", required=True, help="Код трансляції (назва папки)")
    parser.add_argument("--url", default=DEFAULT_RTMP_URL, help="RTMP URL")
    args = parser.parse_args()

    ensure_dirs()
    key = args.key
    url = args.url
    folder = stream_path(key)
    os.makedirs(folder, exist_ok=True)

    while RUNNING:
        files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
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
    return 0

if __name__ == "__main__":
    sys.exit(main())
