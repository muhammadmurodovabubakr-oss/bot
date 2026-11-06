import os
import re
import asyncio
import html
import shutil
import yt_dlp

def get_ffmpeg_path():
    # 1. Tizimda (Linux/Render yoki Docker) ffmpeg bormi tekshiramiz
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg
    # 2. Aks holda imageio_ffmpeg dan olamiz (Windows uchun)
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

FFMPEG_PATH = get_ffmpeg_path()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

YOUTUBE_URL_REGEX = re.compile(
    r'(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|music\.youtube\.com/watch\?v=)([\w\-]+)'
)

def extract_youtube_id(text: str):
    match = YOUTUBE_URL_REGEX.search(text)
    if match:
        return match.group(4)
    return None

def format_duration(seconds):
    if not seconds:
        return "00:00"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def search_music(query: str, limit: int = 5):
    """
    Qo'shiq nomi bo'yicha qidiradi va ro'yxat qaytaradi.
    Hech qanday tashqi API kalit talab qilinmaydi.
    """
    ydl_opts = {
        'extract_flat': True,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }
    
    results = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        search_query = f"ytsearch{limit}:{query}"
        info = ydl.extract_info(search_query, download=False)
        entries = info.get('entries', []) or []
        for entry in entries:
            video_id = entry.get('id')
            title = entry.get('title', "Noma'lum nom")
            duration = entry.get('duration', 0)
            uploader = entry.get('uploader', "Noma'lum ijrochi")
            
            results.append({
                'id': video_id,
                'title': title,
                'escaped_title': html.escape(title),
                'duration': duration,
                'duration_str': format_duration(duration),
                'uploader': uploader,
                'escaped_uploader': html.escape(uploader)
            })
    return results

def download_audio(video_id: str):
    """
    Video ID bo'yicha musiqani yuklab olib MP3 formatiga o'tkazadi.
    """
    target_mp3 = os.path.join(DOWNLOADS_DIR, f"{video_id}.mp3")
    out_template = os.path.join(DOWNLOADS_DIR, f"{video_id}.%(ext)s")

    ydl_opts = {
        'format': 'bestaudio/best',
        'ffmpeg_location': FFMPEG_PATH,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': out_template,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)
        return {
            'file_path': target_mp3,
            'title': info.get('title', 'Musiqa'),
            'uploader': info.get('uploader', "Noma'lum"),
            'duration': info.get('duration', 0)
        }

async def async_search_music(query: str, limit: int = 5):
    return await asyncio.to_thread(search_music, query, limit)

async def async_download_audio(video_id: str):
    return await asyncio.to_thread(download_audio, video_id)
