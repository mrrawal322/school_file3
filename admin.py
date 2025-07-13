from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from models import User, Question, Paper, Notification, Setting, DownloadFile, GalleryImage
from app import db
from datetime import datetime, date
import os
import json

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator to ensure user is admin"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get statistics
    total_teachers = User.query.filter_by(role='teacher').count()
    total_students = User.query.filter_by(role='student').count()
    total_questions = Question.query.count()
    total_papers = Paper.query.count()
    
    # Get recent notifications
    notifications = Notification.query.order_by(Notification.created_at.desc()).limit(5).all()
    
    # Get recent papers
    recent_papers = Paper.query.order_by(Paper.created_at.desc()).limit(5).all()
    
    stats = {
        'teachers': total_teachers,
        'students': total_students,
        'questions': total_questions,
        'papers': total_papers
    }
    
    return render_template('admin/dashboard.html', stats=stats, notifications=notifications, recent_papers=recent_papers)

@admin_bp.route('/teachers')
@login_required
@admin_required
def manage_teachers():
    teachers = User.query.filter_by(role='teacher').all()
    return render_template('admin/manage_teachers.html', teachers=teachers)

@admin_bp.route('/teachers/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_teacher():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        subject = request.form.get('subject')
        class_assigned = request.form.get('class_assigned')
        expiry_date = request.form.get('expiry_date')
        
        if not all([name, email, password, subject]):
            flash('Name, email, password, and subject are required.', 'error')
            return render_template('admin/manage_teachers.html', teachers=User.query.filter_by(role='teacher').all())
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return render_template('admin/manage_teachers.html', teachers=User.query.filter_by(role='teacher').all())
        
        # Convert expiry date
        exp_date = None
        if expiry_date:
            try:
                exp_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format.', 'error')
                return render_template('admin/manage_teachers.html', teachers=User.query.filter_by(role='teacher').all())
        
        teacher = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role='teacher',
            subject=subject,
            class_assigned=class_assigned,
            expiry_date=exp_date,
            is_active=True
        )
        
        db.session.add(teacher)
        db.session.commit()
        
        flash(f'Teacher {name} added successfully.', 'success')
        return redirect(url_for('admin.manage_teachers'))
    
    return render_template('admin/manage_teachers.html', teachers=User.query.filter_by(role='teacher').all())

@admin_bp.route('/teachers/edit/<int:teacher_id>', methods=['POST'])
@login_required
@admin_required
def edit_teacher(teacher_id):
    teacher = User.query.get_or_404(teacher_id)
    
    if teacher.role != 'teacher':
        flash('Invalid teacher ID.', 'error')
        return redirect(url_for('admin.manage_teachers'))
    
    teacher.name = request.form.get('name', teacher.name)
    teacher.email = request.form.get('email', teacher.email)
    teacher.subject = request.form.get('subject', teacher.subject)
    teacher.class_assigned = request.form.get('class_assigned', teacher.class_assigned)
    
    expiry_date = request.form.get('expiry_date')
    if expiry_date:
        try:
            teacher.expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'error')
            return redirect(url_for('admin.manage_teachers'))
    
    # Update password if provided
    new_password = request.form.get('password')
    if new_password:
        teacher.password_hash = generate_password_hash(new_password)
    
    db.session.commit()
    flash(f'Teacher {teacher.name} updated successfully.', 'success')
    return redirect(url_for('admin.manage_teachers'))

@admin_bp.route('/teachers/toggle/<int:teacher_id>')
@login_required
@admin_required
def toggle_teacher(teacher_id):
    teacher = User.query.get_or_404(teacher_id)
    
    if teacher.role != 'teacher':
        flash('Invalid teacher ID.', 'error')
        return redirect(url_for('admin.manage_teachers'))
    
    teacher.is_active = not teacher.is_active
    db.session.commit()
    
    status = 'activated' if teacher.is_active else 'deactivated'
    flash(f'Teacher {teacher.name} {status} successfully.', 'success')
    return redirect(url_for('admin.manage_teachers'))

@admin_bp.route('/teachers/delete/<int:teacher_id>')
@login_required
@admin_required
def delete_teacher(teacher_id):
    teacher = User.query.get_or_404(teacher_id)
    
    if teacher.role != 'teacher':
        flash('Invalid teacher ID.', 'error')
        return redirect(url_for('admin.manage_teachers'))
    
    db.session.delete(teacher)
    db.session.commit()
    
    flash(f'Teacher {teacher.name} deleted successfully.', 'success')
    return redirect(url_for('admin.manage_teachers'))

@admin_bp.route('/students')
@login_required
@admin_required
def manage_students():
    students = User.query.filter_by(role='student').all()
    return render_template('admin/manage_students.html', students=students)

@admin_bp.route('/students/add', methods=['POST'])
@login_required
@admin_required
def add_student():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    class_assigned = request.form.get('class_assigned')
    roll_no = request.form.get('roll_no')
    
    if not all([name, email, password, class_assigned, roll_no]):
        flash('All fields are required.', 'error')
        return redirect(url_for('admin.manage_students'))
    
    # Check if email already exists
    if User.query.filter_by(email=email).first():
        flash('Email already exists.', 'error')
        return redirect(url_for('admin.manage_students'))
    
    student = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        role='student',
        class_assigned=class_assigned,
        roll_no=roll_no,
        is_active=True
    )
    
    db.session.add(student)
    db.session.commit()
    
    flash(f'Student {name} added successfully.', 'success')
    return redirect(url_for('admin.manage_students'))

@admin_bp.route('/students/delete/<int:student_id>')
@login_required
@admin_required
def delete_student(student_id):
    student = User.query.get_or_404(student_id)
    
    if student.role != 'student':
        flash('Invalid student ID.', 'error')
        return redirect(url_for('admin.manage_students'))
    
    db.session.delete(student)
    db.session.commit()
    
    flash(f'Student {student.name} deleted successfully.', 'success')
    return redirect(url_for('admin.manage_students'))

@admin_bp.route('/questions')
@login_required
@admin_required
def manage_questions():
    questions = Question.query.order_by(Question.created_at.desc()).all()
    return render_template('admin/manage_questions.html', questions=questions)

@admin_bp.route('/questions/add', methods=['POST'])
@login_required
@admin_required
def add_question():
    subject = request.form.get('subject')
    class_level = request.form.get('class_level')
    chapter_name = request.form.get('chapter_name')
    chapter_number = request.form.get('chapter_number', type=int)
    question_type = request.form.get('question_type')
    has_parts = request.form.get('has_parts') == 'true'
    
    if not all([subject, class_level, chapter_name, chapter_number, question_type]):
        flash('All required fields must be filled.', 'error')
        return redirect(url_for('admin.manage_questions'))
    
    if has_parts:
        # Handle two-part question
        question_text = request.form.get('question_text_parts')
        part_a_text = request.form.get('part_a_text')
        part_a_marks = request.form.get('part_a_marks', type=int)
        part_b_text = request.form.get('part_b_text')
        part_b_marks = request.form.get('part_b_marks', type=int)
        
        if not all([question_text, part_a_text, part_a_marks, part_b_text, part_b_marks]):
            flash('All parts (A and B) must be completed with their marks.', 'error')
            return redirect(url_for('admin.manage_questions'))
        
        total_marks = part_a_marks + part_b_marks
        
        question = Question(
            subject=subject,
            class_level=class_level,
            chapter_name=chapter_name,
            chapter_number=chapter_number,
            question_type=question_type,
            question_text=question_text,
            marks=total_marks,
            has_parts=True,
            part_a_text=part_a_text,
            part_a_marks=part_a_marks,
            part_b_text=part_b_text,
            part_b_marks=part_b_marks,
            created_by=current_user.id
        )
    else:
        # Handle single question
        question_text = request.form.get('question_text')
        marks = request.form.get('marks', 1, type=int)
        
        if not question_text:
            flash('Question text is required.', 'error')
            return redirect(url_for('admin.manage_questions'))
        
        question = Question(
            subject=subject,
            class_level=class_level,
            chapter_name=chapter_name,
            chapter_number=chapter_number,
            question_type=question_type,
            question_text=question_text,
            marks=marks,
            has_parts=False,
            created_by=current_user.id
        )
    
    # Handle MCQ options (no correct answer required)
    if question_type == 'MCQ' and not has_parts:
        options = []
        for i in range(1, 5):  # 4 options
            option = request.form.get(f'option_{i}')
            if option:
                options.append(option)
        
        if options:
            question.set_options(options)
        else:
            flash('MCQ questions must have options.', 'error')
            return redirect(url_for('admin.manage_questions'))
    
    db.session.add(question)
    db.session.commit()
    
    flash('Question added successfully.', 'success')
    return redirect(url_for('admin.manage_questions'))

@admin_bp.route('/questions/delete/<int:question_id>')
@login_required
@admin_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    
    flash('Question deleted successfully.', 'success')
    return redirect(url_for('admin.manage_questions'))

@admin_bp.route('/notifications')
@login_required
@admin_required
def manage_notifications():
    notifications = Notification.query.order_by(Notification.created_at.desc()).all()
    return render_template('admin/notifications.html', notifications=notifications)

@admin_bp.route('/notifications/add', methods=['POST'])
@login_required
@admin_required
def add_notification():
    title = request.form.get('title')
    message = request.form.get('message')
    target_role = request.form.get('target_role')
    
    if not all([title, message, target_role]):
        flash('All fields are required.', 'error')
        return redirect(url_for('admin.manage_notifications'))
    
    notification = Notification(
        title=title,
        message=message,
        target_role=target_role,
        created_by=current_user.id,
        is_active=True
    )
    
    db.session.add(notification)
    db.session.commit()
    
    flash('Notification created successfully.', 'success')
    return redirect(url_for('admin.manage_notifications'))

@admin_bp.route('/notifications/toggle/<int:notification_id>')
@login_required
@admin_required
def toggle_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    notification.is_active = not notification.is_active
    db.session.commit()
    
    status = 'activated' if notification.is_active else 'deactivated'
    flash(f'Notification {status} successfully.', 'success')
    return redirect(url_for('admin.manage_notifications'))

@admin_bp.route('/settings')
@login_required
@admin_required
def settings():
    return render_template('admin/settings.html')

@admin_bp.route('/settings/update', methods=['POST'])
@login_required
@admin_required
def update_settings():
    academy_name = request.form.get('academy_name')
    
    if academy_name:
        setting = Setting.query.filter_by(key='academy_name').first()
        if setting:
            setting.value = academy_name
        else:
            setting = Setting(key='academy_name', value=academy_name)
            db.session.add(setting)
    
    # Handle logo upload
    if 'logo' in request.files:
        logo_file = request.files['logo']
        if logo_file and logo_file.filename:
            filename = secure_filename(logo_file.filename)
            logo_path = os.path.join('uploads/logos', filename)
            os.makedirs(os.path.dirname(logo_path), exist_ok=True)
            logo_file.save(logo_path)
            
            setting = Setting.query.filter_by(key='academy_logo').first()
            if setting:
                setting.value = logo_path
            else:
                setting = Setting(key='academy_logo', value=logo_path)
                db.session.add(setting)
    
    # Handle background upload
    if 'background' in request.files:
        bg_file = request.files['background']
        if bg_file and bg_file.filename:
            filename = secure_filename(bg_file.filename)
            bg_path = os.path.join('uploads/backgrounds', filename)
            os.makedirs(os.path.dirname(bg_path), exist_ok=True)
            bg_file.save(bg_path)
            
            setting = Setting.query.filter_by(key='background_image').first()
            if setting:
                setting.value = bg_path
            else:
                setting = Setting(key='background_image', value=bg_path)
                db.session.add(setting)
    
    db.session.commit()
    flash('Settings updated successfully.', 'success')
    return redirect(url_for('admin.settings'))
