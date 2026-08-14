from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict

class DifficultyLevel(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"

class CognitiveLevel(str, Enum):
    REMEMBER = "Remember"
    UNDERSTAND = "Understand"
    APPLY = "Apply"
    ANALYZE = "Analyze"

class MCQItem(BaseModel):
    model_config = ConfigDict(extra='ignore')
    
    question: str
    options: Dict[str, str]
    correct_option: str
    explanation: str
    difficulty: Optional[DifficultyLevel] = None
    cognitive_level: Optional[CognitiveLevel] = None

class MCQQuiz(BaseModel):
    model_config = ConfigDict(extra='ignore')
    
    video_id: str
    video_title: str
    video_url: str
    questions: List[MCQItem]

class VideoInfo(BaseModel):
    model_config = ConfigDict(extra='ignore')
    
    id: str
    title: str
    url: str
    duration: Optional[int] = None

class PlaylistMetadata(BaseModel):
    model_config = ConfigDict(extra='ignore')
    
    playlist_title: str
    videos: List[VideoInfo]
