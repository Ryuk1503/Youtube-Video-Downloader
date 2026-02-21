from flask import Flask, render_template, request, jsonify, send_file, Response
import yt_dlp
import os
import uuid
import threading
import time
import re
from pathlib import Path

app = Flask(__name__)

# Thư mục lưu video tạm
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Đường dẫn FFmpeg - sử dụng biến môi trường hoặc None (dùng hệ thống)
FFMPEG_PATH = os.environ.get('FFMPEG_PATH', r"C:\Users\ADMIN\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin")
if os.environ.get('RENDER'):
    FFMPEG_PATH = None  # Render có sẵn FFmpeg trong PATH

# Cookies file path
COOKIES_FILE = Path("cookies.txt")

# Tạo cookies.txt từ environment variable nếu có (dùng cho Render)
COOKIES_ENV = os.environ.get('YOUTUBE_COOKIES')
if COOKIES_ENV:
    with open(COOKIES_FILE, 'w', encoding='utf-8', newline='\n') as f:
        f.write(COOKIES_ENV)

# Lưu trữ tiến trình download
download_progress = {}

def get_yt_dlp_opts():
    """Tạo options cơ bản cho yt-dlp"""
    opts = {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'socket_timeout': 30,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
    }
    
    # Sử dụng cookies nếu có
    if COOKIES_FILE.exists():
        opts['cookiefile'] = str(COOKIES_FILE)
    
    return opts

def extract_video_id(url):
    """Trích xuất video ID từ URL YouTube"""
    patterns = [
        r'(?:v=|/v/|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'(?:embed/)([a-zA-Z0-9_-]{11})',
        r'(?:shorts/)([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_video_info(url):
    """Lấy thông tin video"""
    # Trích xuất video ID để tránh vấn đề với playlist
    video_id = extract_video_id(url)
    if video_id:
        url = f"https://www.youtube.com/watch?v={video_id}"
    
    ydl_opts = get_yt_dlp_opts()
    ydl_opts['extract_flat'] = False
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        return {
            'title': info.get('title'),
            'thumbnail': info.get('thumbnail'),
            'duration': info.get('duration'),
            'channel': info.get('channel') or info.get('uploader'),
            'id': info.get('id'),
            'url': url
        }

def progress_hook(d, download_id):
    """Callback để cập nhật tiến trình"""
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
        downloaded = d.get('downloaded_bytes', 0)
        speed = d.get('speed', 0)
        eta = d.get('eta', 0)
        
        if total > 0:
            percent = (downloaded / total) * 100
        else:
            percent = 0
            
        download_progress[download_id] = {
            'status': 'downloading',
            'percent': round(percent, 1),
            'speed': speed,
            'eta': eta,
            'downloaded': downloaded,
            'total': total
        }
    elif d['status'] == 'finished':
        download_progress[download_id] = {
            'status': 'processing',
            'percent': 100,
            'message': 'Đang xử lý...'
        }

def download_video(url, download_id, format_type='mp4', quality='320'):
    """Download video hoặc audio"""
    try:
        # Trích xuất video ID
        video_id = extract_video_id(url)
        if video_id:
            url = f"https://www.youtube.com/watch?v={video_id}"
        
        output_path = DOWNLOAD_DIR / f"{download_id}.%(ext)s"
        
        # Lấy base options
        ydl_opts = get_yt_dlp_opts()
        ydl_opts['outtmpl'] = str(output_path)
        ydl_opts['progress_hooks'] = [lambda d: progress_hook(d, download_id)]
        
        if format_type == 'mp3':
            # Download audio only
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': str(quality),
            }]
            if FFMPEG_PATH:
                ydl_opts['ffmpeg_location'] = FFMPEG_PATH
        else:
            # Download video + audio with selected quality
            height = int(quality) if quality else 1440
            ydl_opts['format'] = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best'
            ydl_opts['merge_output_format'] = 'mp4'
            ydl_opts['postprocessor_args'] = {
                'merger': ['-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k']
            }
            if FFMPEG_PATH:
                ydl_opts['ffmpeg_location'] = FFMPEG_PATH
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Tìm file đã tải
            ext = 'mp3' if format_type == 'mp3' else 'mp4'
            for possible_ext in [ext, 'mp4', 'mkv', 'webm', 'mp3', 'm4a']:
                potential_file = DOWNLOAD_DIR / f"{download_id}.{possible_ext}"
                if potential_file.exists():
                    download_progress[download_id] = {
                        'status': 'completed',
                        'percent': 100,
                        'filename': str(potential_file),
                        'title': info.get('title', 'video'),
                        'ext': possible_ext
                    }
                    return
            
            # Fallback: tìm bất kỳ file nào với download_id
            for f in DOWNLOAD_DIR.iterdir():
                if f.name.startswith(download_id):
                    download_progress[download_id] = {
                        'status': 'completed',
                        'percent': 100,
                        'filename': str(f),
                        'title': info.get('title', 'video'),
                        'ext': f.suffix[1:]
                    }
                    return
                    
    except Exception as e:
        download_progress[download_id] = {
            'status': 'error',
            'message': str(e)
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/info', methods=['POST'])
def get_info():
    """API lấy thông tin video"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL không hợp lệ'}), 400
        
        info = get_video_info(url)
        return jsonify(info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
def start_download():
    """API bắt đầu download"""
    try:
        data = request.get_json()
        url = data.get('url')
        format_type = data.get('format', 'mp4')  # mp4 hoặc mp3
        quality = data.get('quality', '320' if format_type == 'mp3' else '1440')
        
        if not url:
            return jsonify({'error': 'URL không hợp lệ'}), 400
        
        download_id = str(uuid.uuid4())[:8]
        download_progress[download_id] = {'status': 'starting', 'percent': 0}
        
        # Chạy download trong thread riêng
        thread = threading.Thread(target=download_video, args=(url, download_id, format_type, quality))
        thread.start()
        
        return jsonify({'download_id': download_id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress/<download_id>')
def get_progress(download_id):
    """API kiểm tra tiến trình"""
    progress = download_progress.get(download_id, {'status': 'not_found'})
    return jsonify(progress)

@app.route('/api/file/<download_id>')
def download_file(download_id):
    """API tải file về"""
    progress = download_progress.get(download_id)
    
    if not progress or progress.get('status') != 'completed':
        return jsonify({'error': 'File chưa sẵn sàng'}), 404
    
    filename = progress.get('filename')
    title = progress.get('title', 'video')
    
    if not filename or not os.path.exists(filename):
        return jsonify({'error': 'File không tồn tại'}), 404
    
    # Lấy extension từ filename
    ext = Path(filename).suffix
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()[:100]
    
    return send_file(
        filename,
        as_attachment=True,
        download_name=f"{safe_title}{ext}"
    )

@app.route('/api/cleanup/<download_id>', methods=['DELETE'])
def cleanup(download_id):
    """Xóa file tạm sau khi tải xong"""
    try:
        progress = download_progress.get(download_id)
        if progress and 'filename' in progress:
            filename = progress['filename']
            if os.path.exists(filename):
                os.remove(filename)
        
        if download_id in download_progress:
            del download_progress[download_id]
            
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("🎬 YouTube Video Downloader")
    print(f"📍 Truy cập: http://localhost:{port}")
    print("=" * 40)
    app.run(debug=True, host='0.0.0.0', port=port, threaded=True)
