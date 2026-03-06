from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ytmusicapi import YTMusic
import yt_dlp

app = FastAPI()

# THE CORS FIX: We explicitly whitelist your Vercel site so it doesn't get blocked.
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://r-industries-music-line.vercel.app/"  # <--- REPLACE THIS WITH YOUR REAL VERCEL LINK
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
    # This searches YouTube Music specifically for songs
    results = yt.search(query, filter="songs")
    
    # We clean up the data before sending it to your web app
    clean_results = []
    for item in results[:10]: # Get top 10 results
        # Failsafe for thumbnail keys
        thumbs = item.get("thumbnails") or item.get("thumbnail") or []
        clean_results.append({
            "videoId": item.get("videoId"),
            "title": item.get("title"),
            "artists": [artist["name"] for artist in item.get("artists", [])],
            "thumbnail": thumbs[-1].get("url", "") if thumbs else "",
        })
    return clean_results

@app.get("/stream")
def get_stream(video_id: str):
    # This acts like a stealth agent, extracting the direct audio URL without playing the video
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': 'in_playlist',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
        return {"url": info['url'], "title": info['title']}

@app.get("/radio")
async def get_radio(video_id: str):
    try:
        # Tap directly into the official YouTube Music 'Watch Playlist' algorithm
        radio_data = yt.get_watch_playlist(videoId=video_id, limit=25)
        
        # Format the neural data so the Next.js UI can read it perfectly
        formatted_results = []
        if 'tracks' in radio_data:
            for track in radio_data['tracks']:
                # STRICT VIBE CHECK: Skip the song that is already playing
                if track.get('videoId') == video_id:
                    continue

                # Extract the artist names safely
                artists = [artist['name'] for artist in track.get('artists', [])] if track.get('artists') else ["Unknown Artist"]
                
                # STRICT FAILSAFE: Check for both 'thumbnail' (singular) and 'thumbnails' (plural)
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
        # Taps into the playlist data using the existing ytmusicapi
        playlist = yt.get_playlist(playlist_id, limit=100)
        
        clean_results = []
        for item in playlist.get('tracks', []):
            # Failsafe for thumbnail keys
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