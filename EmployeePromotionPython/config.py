import os
from datetime import timedelta

class Config:
    """إعدادات التطبيق الأساسية"""
    
    # إعدادات قاعدة البيانات
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///employee_promotion.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # إعدادات الأمان
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # إعدادات الجلسة
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # إعدادات التطبيق
    APP_NAME = 'نظام أتمتة العلاوات والترفيعات الوظيفية'
    APP_VERSION = '1.0.0'
    
    # إعدادات التحميل
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    
    # إعدادات التطوير
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    TESTING = False

class DevelopmentConfig(Config):
    """إعدادات بيئة التطوير"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """إعدادات بيئة الإنتاج"""
    DEBUG = False
    SQLALCHEMY_ECHO = False

class TestingConfig(Config):
    """إعدادات بيئة الاختبار"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# قاموس الإعدادات
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

