from fastapi import FastAPI, Request, Body
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
import yt_dlp
import asyncio
import json
import os
from pydantic import BaseModel

app = FastAPI()

# 配置模板和静态文件
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# 创建视频存储目录
VIDEOS_DIR = Path("static/videos")
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

# 存储视频信息的文件
VIDEO_INFO_FILE = "static/video_info.json"

def load_video_info():
    if os.path.exists(VIDEO_INFO_FILE):
        with open(VIDEO_INFO_FILE, "r") as f:
            return json.load(f)
    return []

def save_video_info(info):
    with open(VIDEO_INFO_FILE, "w") as f:
        json.dump(info, f)

# 添加请求模型
class DownloadRequest(BaseModel):
    url: str

@app.get("/")
async def home(request: Request):
    videos = load_video_info()
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "videos": videos}
    )

@app.post("/download")
async def download_video(request: DownloadRequest):
    try:
        # yt-dlp配置
        ydl_opts = {
            'format': 'best',
            'outtmpl': f'{VIDEOS_DIR}/%(title)s.%(ext)s',
            'quiet': True
        }
        
        # 获取视频信息
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            
            # 下载视频
            await asyncio.to_thread(ydl.download, [request.url])
            
            # 保存视频信息
            video_info = {
                'title': info['title'],
                'duration': info['duration'],
                'uploader': info['uploader'],
                'description': info['description'],
                'filename': f"{info['title']}.{info['ext']}",
                'filepath': f"/static/videos/{info['title']}.{info['ext']}"
            }
            
            # 更新视频列表
            videos = load_video_info()
            videos.append(video_info)
            save_video_info(videos)
            
            return JSONResponse({"status": "success", "video": video_info})
            
    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=500
        )

@app.get("/video/{filename}")
async def get_video(filename: str):
    video_path = VIDEOS_DIR / filename
    return FileResponse(video_path)
