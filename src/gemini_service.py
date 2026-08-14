import json
from google import genai
from google.genai import types

def generate_mcqs(api_key, transcript_text, mode='generate', count=5, difficulty='Medium', language='English', custom_instructions='') -> tuple[list[dict] | None, str | None]:
    try:
        client = genai.Client(api_key=api_key)
        
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "options": {
                        "type": "object",
                        "properties": {
                            "A": {"type": "string"},
                            "B": {"type": "string"},
                            "C": {"type": "string"},
                            "D": {"type": "string"}
                        },
                        "required": ["A", "B", "C", "D"]
                    },
                    "correct_option": {"type": "string"},
                    "explanation": {"type": "string"},
                    "difficulty": {"type": "string"},
                    "cognitive_level": {"type": "string"}
                },
                "required": ["question", "options", "correct_option", "explanation"]
            }
        }

        if mode == 'generate':
            system_instruction = f"Generate {count} multiple choice questions (MCQs) of {difficulty} difficulty in {language} based on the provided text. Ensure they accurately reflect the content. {custom_instructions}"
            temperature = 0.5
        else:
            system_instruction = f"Extract {count} existing multiple choice questions (MCQs) directly from the provided transcript if they exist. Translate them to {language} if necessary. {custom_instructions}"
            temperature = 0.2

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=schema,
            temperature=temperature,
        )

        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=transcript_text,
            config=config
        )

        questions_list = json.loads(response.text)
        return questions_list, None
        
    except Exception as e:
        return None, str(e)
