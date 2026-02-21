# 🎬 YouTube Video Downloader

Ứng dụng web chạy local để tải video YouTube miễn phí, nhanh và hỗ trợ chất lượng cao đến **1440p60 FPS**.

## ✨ Tính năng

- 🚀 **Tốc độ cao** - Tải trực tiếp về máy với full băng thông
- 🎥 **Chất lượng cao** - Hỗ trợ 360p, 480p, 720p, 1080p, 1440p (60fps)
- 💯 **Hoàn toàn miễn phí** - Không quảng cáo, không giới hạn
- 🖥️ **Chạy local** - Không cần thuê server
- 🎨 **Giao diện đẹp** - Dark mode, responsive

## 📋 Yêu cầu

- Python 3.8 trở lên
- FFmpeg (để merge video + audio cho chất lượng cao)

## 🚀 Cài đặt

### Bước 1: Cài đặt FFmpeg

#### Windows:
```bash
# Dùng winget (Windows 10/11)
winget install FFmpeg

# Hoặc dùng Chocolatey
choco install ffmpeg

# Hoặc tải từ: https://ffmpeg.org/download.html
```

#### macOS:
```bash
brew install ffmpeg
```

#### Linux:
```bash
sudo apt install ffmpeg  # Ubuntu/Debian
sudo dnf install ffmpeg  # Fedora
```

### Bước 2: Cài đặt thư viện Python

```bash
pip install -r requirements.txt
```

### Bước 3: Chạy ứng dụng

```bash
python app.py
```

Truy cập: **http://localhost:5000**

## 📖 Hướng dẫn sử dụng

1. Mở trình duyệt và truy cập `http://localhost:5000`
2. Dán link video YouTube vào ô tìm kiếm
3. Nhấn **Tìm kiếm** để lấy thông tin video
4. Chọn chất lượng mong muốn (720p, 1080p, 1440p...)
5. Nhấn **Tải video** và đợi
6. Video sẽ tự động tải về máy

## ⚠️ Lưu ý

- Ứng dụng này chỉ dành cho mục đích cá nhân
- Video sẽ được lưu tạm trong thư mục `downloads/` và tự động xóa sau 30s
- Một số video có thể bị giới hạn theo vùng địa lý
- Chất lượng 1080p trở lên yêu cầu FFmpeg để merge video + audio

## 🛠️ Cấu trúc project

```
Youtube Video Download/
├── app.py              # Backend Flask + yt-dlp
├── requirements.txt    # Thư viện cần cài
├── README.md          # Hướng dẫn
├── downloads/         # Thư mục tạm lưu video
└── templates/
    └── index.html     # Giao diện web
```

## 📃 License

MIT License - Sử dụng tự do cho mục đích cá nhân.
