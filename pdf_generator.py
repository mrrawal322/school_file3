from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from models import Question, Setting
import os
from datetime import datetime

def generate_paper_pdf(paper):
    """Generate PDF for the given paper"""
    
    # Create PDF directory if it doesn't exist
    pdf_dir = 'uploads/papers'
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Generate filename
    filename = f'paper_{paper.id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    filepath = os.path.join(pdf_dir, filename)
    
    # Create the PDF document
    doc = SimpleDocTemplate(filepath, pagesize=A4, topMargin=1*inch, bottomMargin=1*inch)
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=12,
        alignment=TA_CENTER,
        spaceAfter=10
    )
    
    question_style = ParagraphStyle(
        'Question',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=10,
        leftIndent=0
    )
    
    # Build the content
    story = []
    
    # Add logo if provided
    if paper.logo_path and os.path.exists(paper.logo_path):
        try:
            logo = Image(paper.logo_path, width=1*inch, height=1*inch)
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 12))
        except:
            pass  # Skip logo if there's an error
    
    # Get academy name from settings
    academy_name = 'Bright Star Academy'
    academy_setting = Setting.query.filter_by(key='academy_name').first()
    if academy_setting and academy_setting.value:
        academy_name = academy_setting.value
    
    # Header information
    story.append(Paragraph(academy_name, title_style))
    story.append(Paragraph(f"Subject: {paper.subject}", header_style))
    story.append(Paragraph(f"Class: {paper.class_level}", header_style))
    story.append(Paragraph(f"Time: {paper.time_allowed} minutes", header_style))
    story.append(Paragraph(f"Total Marks: {paper.total_marks}", header_style))
    
    if paper.student_name:
        story.append(Paragraph(f"Student: {paper.student_name}", header_style))
    
    story.append(Spacer(1, 20))
    
    # Instructions
    instructions = [
        "1. Read all questions carefully before answering.",
        "2. Write your answers clearly and legibly.",
        "3. For MCQs, select the best option.",
        "4. Manage your time wisely."
    ]
    
    story.append(Paragraph("<b>Instructions:</b>", styles['Heading3']))
    for instruction in instructions:
        story.append(Paragraph(instruction, styles['Normal']))
    
    story.append(Spacer(1, 20))
    
    # Add questions
    question_ids = paper.get_question_ids()
    questions = Question.query.filter(Question.id.in_(question_ids)).all()
    
    # Group questions by type
    mcq_questions = [q for q in questions if q.question_type == 'MCQ']
    short_questions = [q for q in questions if q.question_type == 'Short']
    long_questions = [q for q in questions if q.question_type == 'Long']
    
    question_number = 1
    
    # MCQ Section
    if mcq_questions:
        story.append(Paragraph("<b>Section A: Multiple Choice Questions</b>", styles['Heading3']))
        story.append(Spacer(1, 10))
        
        for question in mcq_questions:
            story.append(Paragraph(f"<b>Q{question_number}.</b> {question.question_text} <b>({question.marks} mark{'s' if question.marks > 1 else ''})</b>", question_style))
            
            options = question.get_options()
            if options:
                for i, option in enumerate(options, 1):
                    story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{chr(96+i)}) {option}", styles['Normal']))
            
            story.append(Spacer(1, 10))
            question_number += 1
        
        story.append(Spacer(1, 20))
    
    # Short Questions Section
    if short_questions:
        story.append(Paragraph("<b>Section B: Short Questions</b>", styles['Heading3']))
        story.append(Spacer(1, 10))
        
        for question in short_questions:
            story.append(Paragraph(f"<b>Q{question_number}.</b> {question.question_text} <b>({question.marks} mark{'s' if question.marks > 1 else ''})</b>", question_style))
            story.append(Spacer(1, 30))  # Space for answer
            question_number += 1
        
        story.append(Spacer(1, 20))
    
    # Long Questions Section
    if long_questions:
        story.append(Paragraph("<b>Section C: Long Questions</b>", styles['Heading3']))
        story.append(Spacer(1, 10))
        
        for question in long_questions:
            story.append(Paragraph(f"<b>Q{question_number}.</b> {question.question_text} <b>({question.marks} mark{'s' if question.marks > 1 else ''})</b>", question_style))
            story.append(Spacer(1, 60))  # More space for answer
            question_number += 1
    
    # Build PDF with watermark
    if paper.watermark:
        doc.build(story, onFirstPage=lambda canvas, doc: add_watermark(canvas, doc, paper.watermark),
                  onLaterPages=lambda canvas, doc: add_watermark(canvas, doc, paper.watermark))
    else:
        # Use academy name as default watermark
        doc.build(story, onFirstPage=lambda canvas, doc: add_watermark(canvas, doc, academy_name),
                  onLaterPages=lambda canvas, doc: add_watermark(canvas, doc, academy_name))
    
    return filepath

def add_watermark(canvas, doc, watermark_text):
    """Add watermark to the page"""
    canvas.saveState()
    canvas.setFont('Helvetica', 50)
    canvas.setFillColorRGB(0.8, 0.8, 0.8, alpha=0.3)
    
    # Calculate position for center of page
    page_width = letter[0]
    page_height = letter[1]
    
    # Rotate and draw watermark
    canvas.translate(page_width/2, page_height/2)
    canvas.rotate(45)
    canvas.drawCentredText(0, 0, watermark_text)
    
    canvas.restoreState()
