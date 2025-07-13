# Bright Star Academy - Educational Web Portal

## Overview

Bright Star Academy is a Flask-based educational management system designed for schools and academies. The platform provides role-based access for administrators, teachers, and students, with features for question bank management, exam paper generation, user management, and notifications.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: Flask-Login with role-based access control
- **Template Engine**: Jinja2
- **File Handling**: Werkzeug for secure file uploads

### Frontend Architecture
- **Templates**: HTML with Jinja2 templating
- **CSS Framework**: Bootstrap 5 for responsive design
- **Icons**: Font Awesome for UI icons
- **JavaScript**: Vanilla JS with Bootstrap components

### Database Design
The system uses SQLAlchemy models with the following key entities:
- **User**: Handles admin, teacher, and student accounts with role-based fields
- **Question**: Stores examination questions with chapter info, 2-part support (A&B), and metadata
- **Paper**: Represents generated exam papers with configuration details
- **Notification**: System-wide announcements and messages
- **Setting**: Academy branding and configuration options
- **DownloadFile**: Admin-controlled file sharing system for students/teachers
- **GalleryImage**: Homepage showcase and portfolio image management

## Key Components

### Authentication System
- Role-based login (admin/teacher/student)
- Password hashing using Werkzeug
- Account expiry tracking for teachers
- Account activation/deactivation controls

### Admin Portal (Complete Control)
- User management (teachers and students)
- Question bank administration with chapter-based organization
- Support for 2-part questions (A&B) with separate marks
- File upload and download management system
- Gallery image management for homepage showcase
- System settings and branding
- Notification management
- Dashboard with system statistics

### Teacher Portal
- Exam paper generation with PDF output
- Access to admin-uploaded files (datesheets, resources)
- Personal dashboard with statistics
- Access to notifications

### Student Portal
- View and download available exam papers
- Access to class-specific and general files uploaded by admin
- Personal profile management
- Class-specific content filtering

### PDF Generation
- Uses ReportLab library for PDF creation
- Customizable paper templates
- Watermarking support
- Professional formatting with school branding

## Data Flow

1. **Authentication Flow**: Users log in through a centralized auth system that redirects based on role
2. **Question Management**: Teachers/admins create questions that feed into the central question bank
3. **Paper Generation**: Teachers configure exam parameters, system selects questions, generates PDF
4. **Student Access**: Students view papers filtered by their class assignment
5. **Notification System**: Admins broadcast messages to specific user roles

## External Dependencies

### Python Packages
- Flask: Web framework
- Flask-SQLAlchemy: Database ORM
- Flask-Login: User session management
- Werkzeug: Password hashing and file utilities
- ReportLab: PDF generation
- Pillow (PIL): Image processing

### Frontend Libraries
- Bootstrap 5: CSS framework (CDN)
- Font Awesome: Icon library (CDN)
- jQuery: JavaScript utilities (implied by Bootstrap usage)

### File Storage
- Local file system for uploaded images and generated PDFs
- Uploads directory structure for organized file management

## Deployment Strategy

### Current Setup
- **Platform**: Replit hosting (free tier)
- **Database**: SQLite file-based database
- **Static Files**: Served directly by Flask
- **Environment**: Development mode with debug enabled

### Configuration
- Environment variables for database URL and session secrets
- Configurable upload limits and file paths
- Database connection pooling for reliability

### Security Considerations
- CSRF protection through Flask's built-in features
- Secure filename handling for uploads
- Role-based access decorators
- Password hashing for user credentials

The application follows a traditional MVC pattern with Flask blueprints for modular organization, making it easy to maintain and extend functionality for each user role.