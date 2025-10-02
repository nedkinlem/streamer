import os, json, time, subprocess

STREAMS_DIR = os.path.join(os.getcwd(), "streams")
RUN_DIR     = os.path.join(os.getcwd(), "run")
LOGS_DIR    = os.path.join(os.getcwd(), "logs")

# Європейський ingest сервер YouTube
DEFAULT_RTMP_URL = "rtmp://eu1.rtmp.youtube.com/live2"

def ensure_dirs():
    os.makedirs(STREAMS_DIR, exist_ok=True)
    os.makedirs(RUN_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)

def stream_path(stream_key: str): return os.path.join(STREAMS_DIR, stream_key)
def pidfile_path(stream_key: str): return os.path.join(RUN_DIR, f"{stream_key}.pid")
def logfile_path(stream_key: str): return os.path.join(LOGS_DIR, f"{stream_key}.log")

def write_pid(key, pid): open(pidfile_path(key),"w").write(str(pid))
def read_pid(key):
    p = pidfile_path(key)
    if not os.path.exists(p): return None
    try:
        pid = int(open(p).read().strip())
        os.kill(pid,0)
        return pid
    except: return None
def clear_pid(key):
    try: os.remove(pidfile_path(key))
    except: pass

def list_video_files(folder):
    exts = (".mp4",".mov",".mkv",".avi",".flv",".webm",".ts",".mpeg")
    return sorted([f for f in os.listdir(folder) if f.lower().endswith(exts)])

def run_json(cmd):
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode!=0: return None
    try: return json.loads(proc.stdout)
    except: return None

def get_fps(file):
    d = run_json(["ffprobe","-v","error","-select_streams","v:0",
                  "-show_entries","stream=r_frame_rate","-of","json",file])
    try:
        r = d["streams"][0]["r_frame_rate"]
        num,den = map(int,r.split("/"))
        return int(round(num/den))
    except: return 30

def get_resolution(file):
    d = run_json(["ffprobe","-v","error","-select_streams","v:0",
                  "-show_entries","stream=width,height","-of","json",file])
    try:
        w = d["streams"][0]["width"]
        h = d["streams"][0]["height"]
        return int(w), int(h)
    except: return 1280, 720

def select_bitrate(file):
    """Автовибір бітрейта на основі роздільності та fps"""
    w,h = get_resolution(file)
    fps = get_fps(file)
    if h <= 720:
        return "4000k"
    elif h <= 1080:
        return "6000k" if fps <= 30 else "8000k"
    elif h <= 1440:
        return "12000k"
    else:
        return "20000k"

def is_youtube_compatible(f):
    v = run_json(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=codec_name","-of","json",f])
    a = run_json(["ffprobe","-v","error","-select_streams","a:0","-show_entries","stream=codec_name","-of","json",f])
    if not v or not a: return False
    return v["streams"][0]["codec_name"]=="h264" and a["streams"][0]["codec_name"]=="aac" and f.endswith(".mp4")

def reencode_to_youtube(src):
    base,_=os.path.splitext(src)
    out=f"{base}_yt.mp4"
    fps=get_fps(src); gop=fps*2
    br=select_bitrate(src)
    cmd=["ffmpeg","-y","-i",src,"-c:v","libx264","-preset","veryfast","-b:v",br,
         "-maxrate",br,"-bufsize",str(int(br[:-1])*2)+"k","-g",str(gop),"-keyint_min",str(gop),
         "-tune","zerolatency",
         "-c:a","aac","-b:a","128k","-ar","44100",out]
    if subprocess.call(cmd)==0 and os.path.exists(out):
        os.remove(src)
        return out
    return None

def stream_video(f, url, key):
    fps = get_fps(f); gop = fps * 2

    if is_youtube_compatible(f):
        # Якщо файл вже h264+aac → стрімимо напряму без перекодування
        cmd = [
            "ffmpeg","-re","-i",f,
            "-c:v","copy","-c:a","copy",
            "-f","flv",f"{url}/{key}"
        ]
    else:
        # Інакше перекодовуємо
        br = select_bitrate(f)
        cmd = [
            "ffmpeg","-re","-i",f,
            "-c:v","libx264","-preset","veryfast","-b:v",br,
            "-maxrate",br,"-bufsize",str(int(br[:-1])*2)+"k",
            "-g",str(gop),"-keyint_min",str(gop),
            "-tune","zerolatency","-x264opts",f"keyint={gop}:min-keyint={gop}:no-scenecut",
            "-c:a","aac","-b:a","128k","-ar","44100",
            "-f","flv",f"{url}/{key}"]
    return subprocess.call(cmd)

def estimate_capacity():
    """
    Рахує оціночну кількість можливих стрімів у режимі copy (без перекодування),
    виходячи з пропускної здатності мережі.
    """
    MAX_BPS = 1_000_000_000
    STREAM_BPS = 6_000_000  # ~6 Мбіт/с на один стрім

    def read_tx():
        total=0
        with open("/proc/net/dev") as f:
            for line in f.readlines()[2:]:
                parts=line.split()
                if len(parts)>=10:
                    total += int(parts[9])  # tx_bytes
        return total

    t0=read_tx(); time.sleep(1); t1=read_tx()
    used = (t1-t0)*8
    free = max(0, MAX_BPS - used)
    cap_net = free // STREAM_BPS

    cores=os.cpu_count() or 4
    cap_cpu = max(1, cores*5)

    return int(min(cap_net, cap_cpu))
