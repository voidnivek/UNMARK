from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
import yt_dlp
import requests
import urllib.parse
from fastapi.responses import StreamingResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: str

@app.get("/")
def serve_frontend():
    return FileResponse("index.html")

@app.post("/api/extract")
def extract_video(request: VideoRequest):
    if not request.url.strip():
        raise HTTPException(status_code=400, detail="Please enter a valid URL.")

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "format": "best[ext=mp4]/best",
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=False)
            
            # Extract direct video URL
            video_url = info.get("url")
            if not video_url and "formats" in info:
                # Fallback: pick the last mp4 format with both audio and video
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
                "download_url": f"/api/download?url={urllib.parse.quote(download_url)}",
                "platform": info.get("extractor_key", "Unknown")
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")
