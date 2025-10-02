import os, sys, json, time, subprocess

STREAMS_DIR = os.path.join(os.getcwd(), "streams")
RUN_DIR     = os.path.join(os.getcwd(), "run")
LOGS_DIR    = os.path.join(os.getcwd(), "logs")

DEFAULT_RTMP_URL = "rtmp://a.rtmp.youtube.com/live2"

def ensure_dirs():
    os.makedirs(STREAMS_DIR, exist_ok=True)
    os.makedirs(RUN_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)

def stream_path(stream_key: str) -> str:
    return os.path.join(STREAMS_DIR, stream_key)

def pidfile_path(stream_key: str) -> str:
    return os.path.join(RUN_DIR, f"{stream_key}.pid")

def logfile_path(stream_key: str) -> str:
    return os.path.join(LOGS_DIR, f"{stream_key}.log")

def run_json(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except Exception:
        return None

def get_fps(filepath: str) -> int:
    try:
        data = run_json([
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate",
            "-of", "json", filepath
        ])
        if not data or "streams" not in data or not data["streams"]:
            return 30
        rate = data["streams"][0]["r_frame_rate"]
        if rate and "/" in rate:
            num, den = rate.split("/")
            fps = float(num) / float(den)
            return int(round(fps))
        return 30
    except Exception:
        return 30

def is_youtube_compatible(filepath: str) -> bool:
    v = run_json(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=codec_name","-of","json",filepath])
    a = run_json(["ffprobe","-v","error","-select_streams","a:0","-show_entries","stream=codec_name","-of","json",filepath])
    if not v or not a: return False
    vcodec = v["streams"][0]["codec_name"] if v.get("streams") else ""
    acodec = a["streams"][0]["codec_name"] if a.get("streams") else ""
    return vcodec == "h264" and acodec == "aac" and filepath.lower().endswith(".mp4")

def reencode_to_youtube(src: str) -> str | None:
    base, _ = os.path.splitext(src)
    out = f"{base}_yt.mp4"
    fps = get_fps(src)
    gop = fps * 2
    cmd = [
        "ffmpeg","-y","-i",src,
        "-c:v","libx264","-preset","veryfast","-b:v","4000k","-maxrate","4000k","-bufsize","8000k",
        "-g",str(gop),"-keyint_min",str(gop),
        "-c:a","aac","-b:a","128k","-ar","44100",
        out
    ]
    code = subprocess.call(cmd)
    if code == 0 and os.path.exists(out):
        try: os.remove(src)
        except Exception: pass
        return out
    return None

def stream_video(video_file, stream_url, stream_key):
    fps = get_fps(video_file)
    gop = fps * 2
    cmd = [
        "ffmpeg", "-re", "-i", video_file,
        "-c:v", "libx264", "-preset", "veryfast",
        "-b:v", "4000k", "-maxrate", "4000k", "-bufsize", "8000k",
        "-g", str(gop), "-keyint_min", str(gop),
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-f", "flv", f"{stream_url}/{stream_key}"
    ]
    return subprocess.call(cmd)
