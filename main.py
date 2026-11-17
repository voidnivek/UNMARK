from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import yt_dlp
import requests
import urllib.parse
app = FastAPI()
app.add_middleware(
CORSMiddleware,
allow_origins=[""],
allow_methods=[""],
allow_headers=["*"],
)
class VideoRequest(BaseModel):
url: str
@app.get("/")
def serve_frontend():
return FileResponse("index.html")
def extract_tiktok_fallback(url: str):
api_url = "tikwm.com"
resp = requests.post(api_url, data={"url": url, "hd": 1}, timeout=15)
data = resp.json()
if data.get("code") == 0 and data.get("data"):
video_data = data["data"]
video_url = video_data.get("hdplay") or video_data.get("play")
if video_url:
return {
"title": video_data.get("title") or "TikTok Video",
"thumbnail": video_data.get("cover", ""),
"download_url": f"/api/download?url={urllib.parse.quote(video_url)}",
"platform": "TikTok"
}
return None
@app.post("/api/extract")
def extract_video(request: VideoRequest):
url = request.url.strip()
if not url:
raise HTTPException(status_code=400, detail="Please enter a valid URL.")
if "tiktok.com" in url.lower():
try:
tiktok_result = extract_tiktok_fallback(url)
if tiktok_result:
return tiktok_result
except Exception:
pass
ydl_opts = {
"quiet": True,
"no_warnings": True,
"format": "best[ext=mp4]/best",
"noplaylist": True,
}
try:
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
info = ydl.extract_info(url, download=False)
video_url = info.get("url")
if not video_url and "formats" in info:
mp4_formats = [
f for f in info["formats"]
if f.get("ext") == "mp4" and f.get("acodec") != "none" and f.get("vcodec") != "none"
]
if mp4_formats:
video_url = mp4_formats[-1].get("url")
if not video_url:
raise HTTPException(status_code=404, detail="Could not extract a direct video link.")
return {
"title": info.get("title", "Video"),
"thumbnail": info.get("thumbnail", ""),
"download_url": f"/api/download?url={urllib.parse.quote(video_url)}",
"platform": info.get("extractor_key", "Unknown")
}
except Exception as e:
raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")
@app.get("/api/download")
def download_video(url: str):
headers = {
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
"Referer": "tiktok.com"
}
try:
r = requests.get(url, headers=headers, stream=True, timeout=30)
r.raise_for_status()
return StreamingResponse(
r.iter_content(chunk_size=1024 * 1024),
media_type="video/mp4",
headers={"Content-Disposition": 'attachment; filename="unmark_video.mp4"'}
)
except Exception as e:
raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")
