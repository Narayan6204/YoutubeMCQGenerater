import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable, RequestBlocked

def extract_playlist_metadata(playlist_url: str) -> list[dict]:
    ydl_opts = {
        'extract_flat': True,
        'ignoreerrors': True,
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
        if not info:
            return []
            
        videos = []
        if 'entries' in info:
            for entry in info['entries']:
                if entry:
                    videos.append({
                        'id': entry.get('id'),
                        'title': entry.get('title'),
                        'url': entry.get('url', f"https://www.youtube.com/watch?v={entry.get('id')}"),
                        'duration': entry.get('duration')
                    })
        else:
            videos.append({
                'id': info.get('id'),
                'title': info.get('title'),
                'url': info.get('webpage_url', playlist_url),
                'duration': info.get('duration')
            })
        return videos

def fetch_transcript(video_id: str, languages=('en', 'hi')) -> tuple[str | None, str | None]:
    max_retries = 3
    base_delay = 2.0
    
    for attempt in range(max_retries):
        try:
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)
            try:
                transcript = transcript_list.find_transcript(languages)
            except NoTranscriptFound:
                try:
                    transcript = transcript_list.find_generated_transcript(languages)
                except NoTranscriptFound:
                    transcript = list(transcript_list)[0]
            
            transcript_data = transcript.fetch()
            text = " ".join([
                t.text if hasattr(t, 'text') else t.get('text', '')
                for t in transcript_data
            ])
            return text, None
            
        except TranscriptsDisabled:
            return None, "Transcripts are disabled for this video."
        except NoTranscriptFound:
            return None, f"No transcript found in languages: {languages}"
        except VideoUnavailable:
            return None, "Video is unavailable."
        except RequestBlocked:
            if attempt < max_retries - 1:
                delay = (base_delay ** attempt) + random.uniform(0.1, 1.0)
                time.sleep(delay)
                continue
            return None, "Too many requests to YouTube API. Rate limit exceeded."
        except Exception as e:
            return None, f"An unexpected error occurred: {str(e)}"
    return None, "Max retries exceeded for fetching transcript."

def fetch_transcripts_batch(video_ids: list[str], languages=('en', 'hi'), max_workers=3) -> dict:
    results = {}
    
    def process_video(video_id):
        time.sleep(random.uniform(1.0, 2.5))
        text, error = fetch_transcript(video_id, languages)
        return video_id, text, error

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_vid = {executor.submit(process_video, vid): vid for vid in video_ids}
        for future in as_completed(future_to_vid):
            vid = future_to_vid[future]
            try:
                vid_result, text, error = future.result()
                results[vid] = {'text': text, 'error': error}
            except Exception as e:
                results[vid] = {'text': None, 'error': str(e)}
                
    return results
