import os
from datetime import datetime
from fpdf import FPDF
import logging

# Colors
COLOR_TITLE = (26, 54, 93)     # #1A365D
COLOR_TEXT = (45, 55, 72)      # #2D3748
COLOR_ACCENT = (49, 130, 206)  # #3182CE
COLOR_GREEN = (47, 133, 90)    # #2F855A
COLOR_GRAY = (74, 85, 104)     # #4A5568

class MCQPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
        
        # Try to register fonts, fallback to helvetica
        try:
            # fpdf2 text shaping
            self.set_text_shaping(True)
            self.font_name_main = "Helvetica"
            self.font_name_hindi = "Helvetica"
            
            if os.path.exists('fonts/NotoSans-Regular.ttf'):
                self.add_font("NotoSans", "", 'fonts/NotoSans-Regular.ttf', uni=True)
                self.font_name_main = "NotoSans"
            
            if os.path.exists('fonts/NotoSansDevanagari-Regular.ttf'):
                self.add_font("NotoSansDevanagari", "", 'fonts/NotoSansDevanagari-Regular.ttf', uni=True)
                self.font_name_hindi = "NotoSansDevanagari"
        except Exception as e:
            logging.warning(f"Failed to load fonts, using Helvetica fallback: {e}")
            self.font_name_main = "Helvetica"
            self.font_name_hindi = "Helvetica"
            
    def header(self):
        if self.page_no() != 1:
            self.set_font(self.font_name_main, 'B', 10)
            self.set_text_color(*COLOR_GRAY)
            self.cell(0, 10, 'YOUTUBE PLAYLIST MCQ BANK', align='C')
            self.ln(10)
            
    def footer(self):
        self.set_y(-15)
        self.set_font(self.font_name_main, 'I', 8)
        self.set_text_color(*COLOR_GRAY)
        self.cell(0, 10, f'Page {self.page_no()}', align='R')

def generate_mcq_pdf(output_path: str, playlist_title: str, video_data: list[dict]) -> None:
    pdf = MCQPDF()
    pdf.set_margins(15, 15, 15)
    
    # Calculate stats
    total_videos = len(video_data)
    total_mcqs = sum(len(video.get('questions', [])) for video in video_data)
    generated_date = datetime.now().strftime("%B %d, %Y")
    
    # COVER PAGE
    pdf.add_page()
    pdf.ln(50)
    pdf.set_font(pdf.font_name_main, 'B', 24)
    pdf.set_text_color(*COLOR_TITLE)
    pdf.cell(0, 20, 'YouTube Playlist MCQ Bank', align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font(pdf.font_name_main, 'I', 16)
    pdf.set_text_color(*COLOR_ACCENT)
    pdf.cell(0, 15, 'Study Material and Question Bank', align='C', new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(10)
    # Horizontal line
    pdf.set_draw_color(*COLOR_ACCENT)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(20)
    
    pdf.set_font(pdf.font_name_main, '', 14)
    pdf.set_text_color(*COLOR_TEXT)
    
    metadata = [
        f"Playlist Name: {playlist_title}",
        f"Generated Date: {generated_date}",
        f"Total Videos: {total_videos}",
        f"Total MCQs: {total_mcqs}"
    ]
    
    for item in metadata:
        pdf.cell(0, 10, item, align='C', new_x="LMARGIN", new_y="NEXT")
        
    # PART I - QUESTIONS
    pdf.add_page()
    pdf.set_font(pdf.font_name_main, 'B', 18)
    pdf.set_text_color(*COLOR_TITLE)
    pdf.cell(0, 15, 'PART I: QUESTIONS', align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    for video in video_data:
        video_title = video.get('video_title', 'Untitled Video')
        video_url = video.get('video_url', '')
        questions = video.get('questions', [])
        
        if not questions:
            continue
            
        pdf.set_font(pdf.font_name_main, 'B', 14)
        pdf.set_text_color(*COLOR_ACCENT)
        pdf.ln(5)
        pdf.multi_cell(0, 10, video_title)
        
        if video_url:
            pdf.set_font(pdf.font_name_main, 'I', 10)
            pdf.set_text_color(*COLOR_ACCENT)
            pdf.cell(0, 5, video_url, link=video_url, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            
        for i, q in enumerate(questions, 1):
            question_text = q.get('question', '')
            options = q.get('options', {})
            
            pdf.set_font(pdf.font_name_main, 'B', 12)
            pdf.set_text_color(*COLOR_TEXT)
            pdf.multi_cell(0, 8, f"Q{i}. {question_text}")
            
            pdf.set_font(pdf.font_name_main, '', 11)
            
            opt_a = options.get('A', '')
            opt_b = options.get('B', '')
            opt_c = options.get('C', '')
            opt_d = options.get('D', '')
            
            line1 = f"(A) {opt_a}    (B) {opt_b}"
            line2 = f"(C) {opt_c}    (D) {opt_d}"
            
            pdf.multi_cell(0, 7, line1)
            pdf.multi_cell(0, 7, line2)
            pdf.ln(5)
            
    # PART II - ANSWER KEY
    pdf.add_page()
    pdf.set_font(pdf.font_name_main, 'B', 18)
    pdf.set_text_color(*COLOR_TITLE)
    pdf.cell(0, 15, 'PART II: ANSWERS & EXPLANATIONS', align='L', new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    for video in video_data:
        video_title = video.get('video_title', 'Untitled Video')
        questions = video.get('questions', [])
        
        if not questions:
            continue
            
        pdf.set_font(pdf.font_name_main, 'B', 14)
        pdf.set_text_color(*COLOR_ACCENT)
        pdf.ln(5)
        pdf.multi_cell(0, 10, video_title)
        pdf.ln(2)
        
        for i, q in enumerate(questions, 1):
            question_text = q.get('question', '')
            correct = q.get('correct_option', '')
            explanation = q.get('explanation', '')
            
            pdf.set_font(pdf.font_name_main, 'B', 12)
            pdf.set_text_color(*COLOR_TEXT)
            pdf.multi_cell(0, 8, f"Q{i}. {question_text}")
            
            pdf.set_font(pdf.font_name_main, 'B', 11)
            pdf.set_text_color(*COLOR_GREEN)
            pdf.multi_cell(0, 7, f"Correct Answer: ({correct})")
            
            if explanation:
                pdf.set_font(pdf.font_name_main, 'I', 11)
                pdf.set_text_color(*COLOR_GRAY)
                pdf.multi_cell(0, 7, f"Explanation: {explanation}")
                
            pdf.ln(5)
            
    try:
        pdf.output(output_path)
    except Exception as e:
        logging.error(f"Error saving PDF: {e}")
