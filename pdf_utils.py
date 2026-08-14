from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
import datetime

class NumberedCanvas(canvas.Canvas):
    """
    Custom canvas to implement a two-pass page numbering system ("Page X of Y")
    and running headers.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # Don't draw headers/footers on the cover page (Page 1)
        if self._pageNumber > 1:
            # Header
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#4A5568"))
            self.drawString(54, 755, "YOUTUBE PLAYLIST MCQ BANK")
            
            # Header line
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 747, letter[0]-54, 747)
            
            # Footer line
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 54, letter[0]-54, 54)
            
            # Footer Page number
            self.setFont("Helvetica", 9)
            self.drawRightString(letter[0] - 54, 38, f"Page {self._pageNumber} of {page_count}")
            self.drawString(54, 38, "Generated via MCQ PDF Generator")
            
        else:
            # Cover page footer
            self.setFont("Helvetica", 9)
            self.setFillColor(colors.HexColor("#718096"))
            self.drawCentredString(letter[0]/2.0, 36, "Generated using Google Gemini API")
            
        self.restoreState()

def generate_mcq_pdf(output_path, playlist_title, video_data):
    """
    Compiles list of videos and their generated MCQs into a professional PDF.
    
    video_data is a list of dicts:
    {
        'video_title': str,
        'video_url': str,
        'questions': [
            {
                'question': str,
                'options': {'A': str, 'B': str, 'C': str, 'D': str},
                'correct_option': str (A/B/C/D),
                'explanation': str
            },
            ...
        ]
    }
    """
    # Create document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,  # Give room for running header
        bottomMargin=72 # Give room for running footer
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Palette
    primary_color = colors.HexColor("#1A365D")  # Slate Blue
    text_color = colors.HexColor("#2D3748")     # Charcoal
    accent_color = colors.HexColor("#3182CE")   # Mid Blue
    
    # Custom Styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=32,
        textColor=primary_color,
        spaceAfter=15,
        alignment=1 # Center
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=30,
        alignment=1 # Center
    )
    
    meta_style = ParagraphStyle(
        'CoverMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#718096"),
        spaceAfter=8,
        alignment=1
    )
    
    h1_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=primary_color,
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'VideoHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=accent_color,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )
    
    q_style = ParagraphStyle(
        'QuestionStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=text_color,
        spaceBefore=8,
        spaceAfter=6,
        keepWithNext=True
    )
    
    opt_style = ParagraphStyle(
        'OptionStyle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=text_color,
        spaceAfter=4
    )
    
    ans_style = ParagraphStyle(
        'AnswerStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2F855A"), # Dark Green
        spaceBefore=4,
        spaceAfter=4,
        keepWithNext=True
    )
    
    exp_style = ParagraphStyle(
        'ExplanationStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=10
    )
    
    story = []
    
    # ------------------ COVER PAGE ------------------
    story.append(Spacer(1, 150))
    story.append(Paragraph("YouTube Playlist MCQ Bank", title_style))
    story.append(Paragraph(f"Study Material and Question Bank", subtitle_style))
    
    # Divider line
    story.append(Table(
        [['']],
        colWidths=[letter[0]-108],
        rowHeights=[2],
        style=TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), primary_color),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0),
        ])
    ))
    story.append(Spacer(1, 40))
    
    # Metadata block
    total_videos = len(video_data)
    total_questions = sum(len(v.get('questions', [])) for v in video_data)
    
    story.append(Paragraph(f"<b>Playlist:</b> {playlist_title}", meta_style))
    story.append(Paragraph(f"<b>Generated On:</b> {datetime.datetime.now().strftime('%B %d, %Y')}", meta_style))
    story.append(Paragraph(f"<b>Total Videos Processed:</b> {total_videos}", meta_style))
    story.append(Paragraph(f"<b>Total MCQs Generated:</b> {total_questions}", meta_style))
    story.append(PageBreak())
    
    # ------------------ QUESTIONS SECTION ------------------
    story.append(Paragraph("PART I: QUESTIONS", h1_style))
    story.append(Spacer(1, 10))
    
    q_global_counter = 1
    for v_idx, video in enumerate(video_data, 1):
        questions = video.get('questions', [])
        if not questions:
            continue
            
        story.append(Paragraph(f"Video {v_idx}: {video['video_title']}", h2_style))
        # Optional source link
        story.append(Paragraph(f"<font color='#718096'>Source: <a href='{video['video_url']}'><font color='#3182CE'>{video['video_url']}</font></a></font>", opt_style))
        story.append(Spacer(1, 5))
        
        for q_idx, q in enumerate(questions, 1):
            q_elements = []
            
            # Question text
            q_text = f"<b>Q{q_global_counter}.</b> {q.get('question', '')}"
            q_elements.append(Paragraph(q_text, q_style))
            
            # Options A, B, C, D
            opts = q.get('options', {})
            for key in ['A', 'B', 'C', 'D']:
                opt_val = opts.get(key, '')
                # Using standard bullet indentation format
                opt_paragraph = Paragraph(f"<b>({key})</b> {opt_val}", opt_style)
                q_elements.append(opt_paragraph)
                
            q_elements.append(Spacer(1, 10))
            
            # Keep question and its options on the same page
            story.append(KeepTogether(q_elements))
            q_global_counter += 1
            
        story.append(Spacer(1, 15))
        
    # ------------------ ANSWERS & EXPLANATIONS ------------------
    story.append(PageBreak())
    story.append(Paragraph("PART II: ANSWERS & EXPLANATIONS", h1_style))
    story.append(Spacer(1, 10))
    
    ans_global_counter = 1
    for v_idx, video in enumerate(video_data, 1):
        questions = video.get('questions', [])
        if not questions:
            continue
            
        story.append(Paragraph(f"Video {v_idx}: {video['video_title']}", h2_style))
        story.append(Spacer(1, 5))
        
        for q_idx, q in enumerate(questions, 1):
            ans_elements = []
            
            # Brief question display for context
            ans_elements.append(Paragraph(f"<b>Q{ans_global_counter}.</b> {q.get('question', '')}", q_style))
            
            # Correct Option
            correct_opt = q.get('correct_option', '').strip()
            # If the option text is available, show it too
            correct_opt_text = q.get('options', {}).get(correct_opt, '')
            ans_str = f"Correct Answer: ({correct_opt})"
            if correct_opt_text:
                ans_str += f" - {correct_opt_text}"
            ans_elements.append(Paragraph(ans_str, ans_style))
            
            # Explanation
            explanation = q.get('explanation', 'No explanation provided.')
            ans_elements.append(Paragraph(f"<b>Explanation:</b> {explanation}", exp_style))
            ans_elements.append(Spacer(1, 8))
            
            story.append(KeepTogether(ans_elements))
            ans_global_counter += 1
            
        story.append(Spacer(1, 15))
        
    # Build Document using NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
