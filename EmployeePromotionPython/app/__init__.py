from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config

# إنشاء مثيلات الإضافات
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name='default'):
    """
    مصنع التطبيق - إنشاء وتكوين تطبيق Flask
    
    Args:
        config_name: اسم التكوين المطلوب
        
    Returns:
        تطبيق Flask مكون
    """
    app = Flask(__name__)
    
    # تحميل التكوين
    app.config.from_object(config[config_name])
    
    # تهيئة الإضافات
    db.init_app(app)
    migrate.init_app(app, db)
    
    # تسجيل المخططات (Blueprints)
    from .routes import main_bp, employee_bp, event_bp, report_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(employee_bp, url_prefix='/employees')
    app.register_blueprint(event_bp, url_prefix='/events')
    app.register_blueprint(report_bp, url_prefix='/reports')
    
    # إنشاء الجداول
    with app.app_context():
        db.create_all()
    
    # معالج الأخطاء
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # فلاتر القوالب المخصصة
    @app.template_filter('arabic_date')
    def arabic_date_filter(date_obj):
        """تحويل التاريخ إلى تنسيق عربي"""
        if not date_obj:
            return ''
        return date_obj.strftime('%d/%m/%Y')
    
    @app.template_filter('days_from_now')
    def days_from_now_filter(date_obj):
        """حساب عدد الأيام من اليوم"""
        if not date_obj:
            return 0
        from datetime import date
        return (date_obj - date.today()).days
    
    return app

