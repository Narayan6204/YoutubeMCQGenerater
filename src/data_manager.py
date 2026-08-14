import os
import json
import logging

DRAFTS_DIR = 'mcq_drafts'
METADATA_FILE = os.path.join(DRAFTS_DIR, 'playlist_metadata.json')

def ensure_drafts_dir():
    try:
        os.makedirs(DRAFTS_DIR, exist_ok=True)
    except Exception as e:
        logging.error(f"Error creating drafts directory: {e}")

def save_draft(quiz_data: dict):
    ensure_drafts_dir()
    video_id = quiz_data.get('video_id')
    if not video_id:
        logging.error("No video_id in quiz_data")
        return
    
    file_path = os.path.join(DRAFTS_DIR, f"{video_id}.json")
    try:
        # Atomic write pattern: write to a temp file and rename
        temp_path = f"{file_path}.tmp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(quiz_data, f, ensure_ascii=False, indent=4)
        os.replace(temp_path, file_path)
    except Exception as e:
        logging.error(f"Error saving draft for video_id {video_id}: {e}")

def load_draft(video_id: str) -> dict | None:
    file_path = os.path.join(DRAFTS_DIR, f"{video_id}.json")
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading draft {video_id}: {e}")
        return None

def list_drafts() -> list[dict]:
    ensure_drafts_dir()
    drafts = []
    try:
        for filename in os.listdir(DRAFTS_DIR):
            if filename.endswith('.json') and filename != 'playlist_metadata.json':
                video_id = filename[:-5]
                draft = load_draft(video_id)
                if draft:
                    drafts.append(draft)
    except Exception as e:
        logging.error(f"Error listing drafts: {e}")
    return drafts

def delete_draft(video_id: str) -> bool:
    file_path = os.path.join(DRAFTS_DIR, f"{video_id}.json")
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        logging.error(f"Error deleting draft {video_id}: {e}")
        return False

def get_processed_ids() -> set[str]:
    ensure_drafts_dir()
    processed_ids = set()
    try:
        for filename in os.listdir(DRAFTS_DIR):
            if filename.endswith('.json') and filename != 'playlist_metadata.json':
                processed_ids.add(filename[:-5])
    except Exception as e:
        logging.error(f"Error getting processed ids: {e}")
    return processed_ids

def save_playlist_metadata(videos: list, playlist_title: str):
    ensure_drafts_dir()
    try:
        temp_path = f"{METADATA_FILE}.tmp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump({'videos': videos, 'playlist_title': playlist_title}, f, ensure_ascii=False, indent=4)
        os.replace(temp_path, METADATA_FILE)
    except Exception as e:
        logging.error(f"Error saving playlist metadata: {e}")

def load_playlist_metadata() -> tuple[list, str]:
    if not os.path.exists(METADATA_FILE):
        return [], 'YouTube MCQ Bank'
    try:
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('videos', []), data.get('playlist_title', 'YouTube MCQ Bank')
    except Exception as e:
        logging.error(f"Error loading playlist metadata: {e}")
        return [], 'YouTube MCQ Bank'
