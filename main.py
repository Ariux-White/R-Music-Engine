from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ytmusicapi import YTMusic
import yt_dlp

app = FastAPI()

# Robust CORS Configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://r-industries-music-line.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

yt = YTMusic()

@app.get("/")
def read_root():
    return {"status": "R-Stream Engine Online"}

@app.get("/search")
def search_music(query: str):
    try:
        results = yt.search(query, filter="songs")
        clean_results = []
        for item in results[:10]:
            thumbs = item.get("thumbnails") or item.get("thumbnail") or []
            clean_results.append({
                "videoId": item.get("videoId"),
                "title": item.get("title"),
                "artists": [artist["name"] for artist in item.get("artists", [])],
                "thumbnail": thumbs[-1].get("url", "") if thumbs else "",
            })
        return clean_results
    except Exception as e:
        return {"error": str(e)}

@app.get("/stream")
def get_stream(video_id: str):
    # STEALTH UPGRADE: Pretending to be a real browser to avoid the 403/Video Unavailable error
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'addheader': [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            return {"url": info['url'], "title": info['title']}
    except Exception as e:
        # Failsafe: return the error so we can see it in the UI
        return {"error": str(e)}

@app.get("/radio")
async def get_radio(video_id: str):
    try:
        radio_data = yt.get_watch_playlist(videoId=video_id, limit=25)
        formatted_results = []
        if 'tracks' in radio_data:
            for track in radio_data['tracks']:
                if track.get('videoId') == video_id:
                    continue
                artists = [artist['name'] for artist in track.get('artists', [])] if track.get('artists') else ["Unknown Artist"]
                thumbs = track.get('thumbnail') or track.get('thumbnails') or []
                thumbnail_url = thumbs[-1]['url'] if isinstance(thumbs, list) and len(thumbs) > 0 else ""
                if track.get('videoId'):
                    formatted_results.append({
                        "videoId": track.get('videoId'),
                        "title": track.get('title', 'Unknown Title'),
                        "artists": artists,
                        "thumbnail": thumbnail_url
                    })
        return formatted_results[:20]
    except Exception as e:
        return {"error": str(e)}

@app.get("/playlist")
def get_playlist(playlist_id: str):
    try:
        playlist = yt.get_playlist(playlist_id, limit=100)
        clean_results = []
        for item in playlist.get('tracks', []):
            thumbs = item.get("thumbnails") or item.get("thumbnail") or []
            thumb_url = thumbs[-1].get("url", "") if thumbs else ""
            clean_results.append({
                "videoId": item.get("videoId"),
                "title": item.get("title"),
                "artists": [artist["name"] for artist in item.get("artists", [])] if item.get("artists") else ["Unknown Artist"],
                "thumbnail": thumb_url,
            })
        return {"title": playlist.get("title", "Imported Playlist"), "tracks": clean_results}
    except Exception as e:
        return {"error": str(e)}