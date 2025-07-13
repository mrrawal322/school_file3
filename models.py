from app import db
from flask_login import UserMixin
from datetime import datetime
import json

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, student
    is_active = db.Column(db.Boolean, default=True)
    expiry_date = db.Column(db.Date, nullable=True)  # For teachers
    class_assigned = db.Column(db.String(50), nullable=True)  # For students and teachers
    roll_no = db.Column(db.String(20), nullable=True)  # For students
    subject = db.Column(db.String(100), nullable=True)  # For teachers
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    papers_created = db.relationship('Paper', backref='teacher', lazy=True, foreign_keys='Paper.teacher_id')
    
    def __repr__(self):
        return f'<User {self.email}>'

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    class_level = db.Column(db.String(20), nullable=False)
    chapter_name = db.Column(db.String(100), nullable=False)
    chapter_number = db.Column(db.Integer, nullable=False)
    question_type = db.Column(db.String(20), nullable=False)  # MCQ, Short, Long
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.Text, nullable=True)  # JSON string for MCQ options
    correct_answer = db.Column(db.Text, nullable=True)
    marks = db.Column(db.Integer, default=1)
    # For 2-part questions (especially science subjects)
    part_a_text = db.Column(db.Text, nullable=True)  # Part A question text
    part_a_marks = db.Column(db.Integer, nullable=True)  # Part A marks
    part_b_text = db.Column(db.Text, nullable=True)  # Part B question text
    part_b_marks = db.Column(db.Integer, nullable=True)  # Part B marks
    has_parts = db.Column(db.Boolean, default=False)  # Whether question has A/B parts
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def get_options(self):
        """Get options as a list for MCQ questions"""
        if self.options:
            try:
                return json.loads(self.options)
            except:
                return []
        return []
    
    def set_options(self, options_list):
        """Set options from a list for MCQ questions"""
        self.options = json.dumps(options_list)
    
    def __repr__(self):
        return f'<Question {self.id}: {self.question_text[:50]}>'

class Paper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    class_level = db.Column(db.String(20), nullable=False)
    total_marks = db.Column(db.Integer, nullable=False)
    time_allowed = db.Column(db.Integer, nullable=False)  # in minutes
    teacher_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    student_name = db.Column(db.String(100), nullable=True)
    logo_path = db.Column(db.String(200), nullable=True)
    watermark = db.Column(db.String(100), nullable=True)
    question_ids = db.Column(db.Text, nullable=False)  # JSON string of question IDs
    pdf_path = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_question_ids(self):
        """Get question IDs as a list"""
        try:
            return json.loads(self.question_ids)
        except:
            return []
    
    def set_question_ids(self, ids_list):
        """Set question IDs from a list"""
        self.question_ids = json.dumps(ids_list)
    
    def __repr__(self):
        return f'<Paper {self.title}>'

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    target_role = db.Column(db.String(20), nullable=False)  # teacher, student, all
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<Notification {self.title}>'

class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Setting {self.key}: {self.value}>'

class DownloadFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(200), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # pdf, doc, ppt, etc.
    target_role = db.Column(db.String(20), nullable=False)  # teacher, student, all
    class_level = db.Column(db.String(20), nullable=True)  # specific class or null for all
    subject = db.Column(db.String(100), nullable=True)  # specific subject or null for all
    is_active = db.Column(db.Boolean, default=True)
    download_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<DownloadFile {self.title}>'

class GalleryImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_path = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # showcase, portfolio, achievement
    is_active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<GalleryImage {self.title}>'
