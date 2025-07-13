from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import User, Question, Paper, Notification
from app import db
from pdf_generator import generate_paper_pdf
from datetime import date
import os
import json

teacher_bp = Blueprint('teacher', __name__)

def teacher_required(f):
    """Decorator to ensure user is teacher"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'teacher':
            flash('Access denied. Teacher privileges required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@teacher_bp.route('/dashboard')
@login_required
@teacher_required
def dashboard():
    # Get teacher's papers
    papers = Paper.query.filter_by(teacher_id=current_user.id).order_by(Paper.created_at.desc()).limit(10).all()
    
    # Get notifications for teachers
    notifications = Notification.query.filter(
        (Notification.target_role == 'teacher') | (Notification.target_role == 'all')
    ).filter_by(is_active=True).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Get statistics
    total_papers = Paper.query.filter_by(teacher_id=current_user.id).count()
    total_questions = Question.query.filter_by(created_by=current_user.id).count()
    
    stats = {
        'papers': total_papers,
        'questions': total_questions
    }
    
    return render_template('teacher/dashboard.html', papers=papers, notifications=notifications, stats=stats, today=date.today())

@teacher_bp.route('/generate-paper', methods=['GET', 'POST'])
@login_required
@teacher_required
def generate_paper():
    if request.method == 'POST':
        title = request.form.get('title')
        subject = request.form.get('subject')
        class_level = request.form.get('class_level')
        total_marks = request.form.get('total_marks', type=int)
        time_allowed = request.form.get('time_allowed', type=int)
        student_name = request.form.get('student_name', '')
        watermark = request.form.get('watermark', '')
        
        # Get selected questions
        selected_questions = request.form.getlist('questions')
        
        if not all([title, subject, class_level, total_marks, time_allowed]):
            flash('All required fields must be filled.', 'error')
            return redirect(url_for('teacher.generate_paper'))
        
        if not selected_questions:
            flash('Please select at least one question.', 'error')
            return redirect(url_for('teacher.generate_paper'))
        
        # Handle logo upload
        logo_path = None
        if 'logo' in request.files:
            logo_file = request.files['logo']
            if logo_file and logo_file.filename:
                filename = secure_filename(logo_file.filename)
                logo_path = os.path.join('uploads/logos', f'paper_{current_user.id}_{filename}')
                os.makedirs(os.path.dirname(logo_path), exist_ok=True)
                logo_file.save(logo_path)
        
        # Create paper record
        paper = Paper(
            title=title,
            subject=subject,
            class_level=class_level,
            total_marks=total_marks,
            time_allowed=time_allowed,
            teacher_id=current_user.id,
            student_name=student_name,
            logo_path=logo_path,
            watermark=watermark
        )
        paper.set_question_ids([int(q) for q in selected_questions])
        
        db.session.add(paper)
        db.session.commit()
        
        # Generate PDF
        try:
            pdf_path = generate_paper_pdf(paper)
            paper.pdf_path = pdf_path
            db.session.commit()
            
            flash('Paper generated successfully!', 'success')
            return redirect(url_for('teacher.view_papers'))
        except Exception as e:
            flash(f'Error generating PDF: {str(e)}', 'error')
            return redirect(url_for('teacher.generate_paper'))
    
    # Get available questions
    questions = Question.query.all()
    subjects = db.session.query(Question.subject).distinct().all()
    classes = db.session.query(Question.class_level).distinct().all()
    
    return render_template('teacher/generate_paper.html', 
                         questions=questions, 
                         subjects=[s[0] for s in subjects],
                         classes=[c[0] for c in classes])

@teacher_bp.route('/papers')
@login_required
@teacher_required
def view_papers():
    papers = Paper.query.filter_by(teacher_id=current_user.id).order_by(Paper.created_at.desc()).all()
    return render_template('teacher/view_papers.html', papers=papers)

@teacher_bp.route('/papers/download/<int:paper_id>')
@login_required
@teacher_required
def download_paper(paper_id):
    paper = Paper.query.get_or_404(paper_id)
    
    # Ensure teacher can only download their own papers
    if paper.teacher_id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('teacher.view_papers'))
    
    if not paper.pdf_path or not os.path.exists(paper.pdf_path):
        flash('PDF file not found.', 'error')
        return redirect(url_for('teacher.view_papers'))
    
    return send_file(paper.pdf_path, as_attachment=True, download_name=f'{paper.title}.pdf')

# Question management moved to admin only

@teacher_bp.route('/downloads')
@login_required
@teacher_required
def downloads():
    """View downloadable files for teachers"""
    from models import DownloadFile
    files = DownloadFile.query.filter(
        (DownloadFile.target_role.in_(['teacher', 'all'])) &
        (DownloadFile.is_active == True)
    ).order_by(DownloadFile.created_at.desc()).all()
    
    return render_template('teacher/downloads.html', files=files)

@teacher_bp.route('/downloads/file/<int:file_id>')
@login_required
@teacher_required
def download_file(file_id):
    """Download a file"""
    from models import DownloadFile
    file = DownloadFile.query.get_or_404(file_id)
    
    # Check if teacher can access this file
    if file.target_role not in ['teacher', 'all'] or not file.is_active:
        flash('Access denied.', 'error')
        return redirect(url_for('teacher.downloads'))
    
    if not os.path.exists(file.file_path):
        flash('File not found.', 'error')
        return redirect(url_for('teacher.downloads'))
    
    # Increment download count
    file.download_count += 1
    db.session.commit()
    
    return send_file(file.file_path, as_attachment=True, download_name=file.title + '.' + file.file_type)

@teacher_bp.route('/profile')
@login_required
@teacher_required
def profile():
    return render_template('teacher/profile.html')
