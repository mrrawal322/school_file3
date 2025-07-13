from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from models import User, Paper, Notification
from app import db
import os

student_bp = Blueprint('student', __name__)

def student_required(f):
    """Decorator to ensure user is student"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            flash('Access denied. Student privileges required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    # Get papers for student's class
    papers = Paper.query.filter_by(class_level=current_user.class_assigned).order_by(Paper.created_at.desc()).all()
    
    # Get notifications for students
    notifications = Notification.query.filter(
        (Notification.target_role == 'student') | (Notification.target_role == 'all')
    ).filter_by(is_active=True).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Filter by subject if requested
    subject_filter = request.args.get('subject')
    if subject_filter:
        papers = [p for p in papers if p.subject == subject_filter]
    
    # Get available subjects for filtering
    subjects = list(set([p.subject for p in Paper.query.filter_by(class_level=current_user.class_assigned).all()]))
    
    return render_template('student/dashboard.html', papers=papers, notifications=notifications, subjects=subjects, current_subject=subject_filter)

@student_bp.route('/papers/download/<int:paper_id>')
@login_required
@student_required
def download_paper(paper_id):
    paper = Paper.query.get_or_404(paper_id)
    
    # Ensure student can only download papers for their class
    if paper.class_level != current_user.class_assigned:
        flash('Access denied.', 'error')
        return redirect(url_for('student.dashboard'))
    
    if not paper.pdf_path or not os.path.exists(paper.pdf_path):
        flash('PDF file not found.', 'error')
        return redirect(url_for('student.dashboard'))
    
    return send_file(paper.pdf_path, as_attachment=True, download_name=f'{paper.title}.pdf')

@student_bp.route('/downloads')
@login_required
@student_required
def downloads():
    """View downloadable files for students"""
    from models import DownloadFile
    files = DownloadFile.query.filter(
        (DownloadFile.target_role.in_(['student', 'all'])) &
        (DownloadFile.is_active == True)
    ).order_by(DownloadFile.created_at.desc()).all()
    
    # Filter by class if specified
    class_files = []
    general_files = []
    
    for file in files:
        if file.class_level and file.class_level == current_user.class_assigned:
            class_files.append(file)
        elif not file.class_level:
            general_files.append(file)
    
    return render_template('student/downloads.html', class_files=class_files, general_files=general_files)

@student_bp.route('/downloads/file/<int:file_id>')
@login_required
@student_required
def download_file(file_id):
    """Download a file"""
    from models import DownloadFile
    file = DownloadFile.query.get_or_404(file_id)
    
    # Check if student can access this file
    if file.target_role not in ['student', 'all'] or not file.is_active:
        flash('Access denied.', 'error')
        return redirect(url_for('student.downloads'))
    
    # Check class restriction
    if file.class_level and file.class_level != current_user.class_assigned:
        flash('This file is not available for your class.', 'error')
        return redirect(url_for('student.downloads'))
    
    if not os.path.exists(file.file_path):
        flash('File not found.', 'error')
        return redirect(url_for('student.downloads'))
    
    # Increment download count
    file.download_count += 1
    db.session.commit()
    
    return send_file(file.file_path, as_attachment=True, download_name=file.title + '.' + file.file_type)

@student_bp.route('/profile')
@login_required
@student_required
def profile():
    return render_template('student/profile.html')
