import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable

def extract_playlist_videos(playlist_url):
    """
    Extracts all video titles, URLs, and IDs from a YouTube playlist URL.
    Uses yt-dlp flat extraction for fast fetching without API keys.
    """
    ydl_opts = {
        'extract_flat': True,
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(playlist_url, download=False)
            if not result:
                return []
            
            # If the link provided is a single video instead of a playlist
            if 'entries' not in result:
                return [{
                    'id': result.get('id'),
                    'title': result.get('title'),
                    'url': f"https://www.youtube.com/watch?v={result.get('id')}"
                }]
            
            videos = []
            for entry in result['entries']:
                if entry:
                    video_id = entry.get('id')
                    title = entry.get('title', 'Unknown Title')
                    # Standardize URL
                    url = f"https://www.youtube.com/watch?v={video_id}" if video_id else entry.get('url')
                    if video_id:
                        videos.append({
                            'id': video_id,
                            'title': title,
                            'url': url
                        })
            return videos
    except Exception as e:
        print(f"Error extracting playlist videos: {e}")
        return []

def get_video_transcript(video_id, languages=('en', 'hi')):
    """
    Fetches the transcript for a given YouTube video ID.
    Attempts to fetch languages in order of preference (default: English, Hindi).
    """
    try:
        # Create an instance of YouTubeTranscriptApi
        api = YouTubeTranscriptApi()
        
        # Retrieve the transcript list to check available languages
        transcript_list = api.list(video_id)
        
        # Try to find a transcript in the preferred languages
        transcript = None
        try:
            transcript = transcript_list.find_transcript(languages)
        except NoTranscriptFound:
            # Fallback to whatever is available (first language)
            try:
                transcript = transcript_list.find_generated_transcript(languages)
            except NoTranscriptFound:
                # If preferred languages aren't found, pick the first manual or auto-generated one
                for t in transcript_list:
                    transcript = t
                    break
        
        if transcript:
            data = transcript.fetch()
            # Combine transcript segments. The latest youtube-transcript-api returns 
            # FetchedTranscriptSnippet objects (dataclasses) instead of dicts.
            full_text = " ".join([entry.text if hasattr(entry, 'text') else entry['text'] for entry in data])
            return full_text, None
        else:
            return None, "No transcript available for this video."

    except TranscriptsDisabled:
        return None, "Transcripts/Subtitles are disabled for this video."
    except VideoUnavailable:
        return None, "This video is unavailable (private, deleted, or region-restricted)."
    except Exception as e:
        return None, f"Failed to retrieve transcript: {str(e)}"
