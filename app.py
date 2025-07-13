import os
import logging
from flask import Flask, render_template, redirect, url_for, session, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "bright-star-academy-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///bright_star_academy.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Import blueprints
from auth import auth_bp
from admin import admin_bp
from teacher import teacher_bp
from student import student_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(teacher_bp, url_prefix='/teacher')
app.register_blueprint(student_bp, url_prefix='/student')

@app.route('/')
def index():
    """Home page - redirect to appropriate dashboard based on user role"""
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'teacher':
            return redirect(url_for('teacher.dashboard'))
        elif current_user.role == 'student':
            return redirect(url_for('student.dashboard'))
    return render_template('index.html')

@app.context_processor
def inject_settings():
    """Inject global settings into all templates"""
    from models import Setting
    settings = {}
    try:
        setting_records = Setting.query.all()
        for setting in setting_records:
            settings[setting.key] = setting.value
    except:
        pass
    
    # Default values
    if 'academy_name' not in settings:
        settings['academy_name'] = 'Bright Star Academy'
    if 'academy_logo' not in settings:
        settings['academy_logo'] = ''
    if 'background_image' not in settings:
        settings['background_image'] = ''
    
    return dict(settings=settings)

# Create database tables
with app.app_context():
    from models import User, Question, Paper, Notification, Setting
    db.create_all()
    
    # Create default admin user if none exists
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        from werkzeug.security import generate_password_hash
        admin_user = User(
            name='Administrator',
            email='admin@brightstar.edu',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            is_active=True
        )
        db.session.add(admin_user)
        
        # Add default settings
        default_settings = [
            Setting(key='academy_name', value='Bright Star Academy'),
            Setting(key='academy_logo', value=''),
            Setting(key='background_image', value='')
        ]
        for setting in default_settings:
            db.session.add(setting)
        
        db.session.commit()
        print("Default admin user created: admin@brightstar.edu / admin123")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
