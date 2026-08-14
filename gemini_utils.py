import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import List, Dict
import json

class MCQ(BaseModel):
    question: str = Field(description="The multiple choice question text")
    options: Dict[str, str] = Field(description="Dictionary with exactly 4 keys: A, B, C, D and their corresponding answer options")
    correct_option: str = Field(description="The correct key, must be exactly one of: A, B, C, D")
    explanation: str = Field(description="Detailed explanation of why this option is correct based on the video context")

class MCQList(BaseModel):
    questions: List[MCQ]

def generate_mcqs_from_transcript(api_key, transcript_text, mode="generate", count=5, difficulty="medium", language="English", custom_instructions=""):
    """
    Calls Gemini API to generate or extract MCQs from a transcript.
    
    Parameters:
    - api_key (str): Gemini API key
    - transcript_text (str): The transcript content of the video
    - mode (str): "generate" to create new MCQs, "extract" to find existing MCQs in the video
    - count (int): Number of questions to generate (only for generate mode)
    - difficulty (str): difficulty level (easy, medium, hard)
    - language (str): language of the questions (e.g. English, Hindi, etc.)
    - custom_instructions (str): extra rules from the user
    
    Returns:
    - list: List of MCQ dicts, or None if failed
    - str: Error message if failed
    """
    if not api_key:
        return None, "Gemini API Key is missing. Please set it in the sidebar."
        
    try:
        genai.configure(api_key=api_key)
        
        # We use gemini-1.5-flash because it is fast, highly stable, and has a large context window.
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        if mode == "generate":
            system_prompt = (
                f"You are an expert educator. Your task is to generate {count} Multiple Choice Questions (MCQs) "
                f"based ONLY on the provided video transcript. The questions should be of '{difficulty}' difficulty "
                f"and written in the '{language}' language.\n"
                f"Ensure each question has exactly 4 options (A, B, C, D), a single correct option, and a clear explanation."
            )
            
            user_prompt = f"Transcript:\n{transcript_text}\n"
            if custom_instructions:
                user_prompt += f"\nCustom Instructions/Formatting Guidelines:\n{custom_instructions}"
                
        else: # extract mode
            system_prompt = (
                f"You are an assistant that extracts questions. Your task is to analyze the provided video transcript "
                f"and extract the Multiple Choice Questions (MCQs) that were ALREADY used, presented, or discussed "
                f"in the video itself (e.g., quizzes, practice tests, or check-for-understanding questions mentioned by the speaker).\n"
                f"If the transcript has questions but they don't have explicit A/B/C/D choices or options, structure them into A/B/C/D choices based on what is described.\n"
                f"For each MCQ, identify the correct option and compile the explanation given by the instructor in the video.\n"
                f"The questions and explanations should be written in '{language}' language.\n"
                f"If there are no MCQs or test questions discussed in the video transcript, return an empty list."
            )
            user_prompt = f"Transcript:\n{transcript_text}\n"
            if custom_instructions:
                user_prompt += f"\nCustom Instructions/Formatting Guidelines:\n{custom_instructions}"
                
        # Send query with schema validation
        response = model.generate_content(
            contents=[system_prompt, user_prompt],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=MCQList,
                temperature=0.1 if mode == "extract" else 0.5
            )
        )
        
        # Parse the JSON response
        data = json.loads(response.text)
        return data.get("questions", []), None
        
    except Exception as e:
        return None, f"Error communicating with Gemini API: {str(e)}"
