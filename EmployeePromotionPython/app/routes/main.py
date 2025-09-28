from flask import Blueprint, render_template, request, jsonify
from ..services import employee_service, professional_event_service, promotion_history_service

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """الصفحة الرئيسية - لوحة التحكم"""
    try:
        # الحصول على الإحصائيات
        employee_stats = employee_service.get_employees_statistics()
        event_stats = professional_event_service.get_events_statistics()
        promotion_stats = promotion_history_service.get_promotion_statistics()
        
        return render_template('index.html',
                             employee_stats=employee_stats,
                             event_stats=event_stats,
                             promotion_stats=promotion_stats)
    except Exception as e:
        return render_template('errors/500.html', error=str(e)), 500

@main_bp.route('/api/dashboard-stats')
def dashboard_stats():
    """API للحصول على إحصائيات لوحة التحكم"""
    try:
        stats = {
            'employees': employee_service.get_employees_statistics(),
            'events': professional_event_service.get_events_statistics(),
            'promotions': promotion_history_service.get_promotion_statistics()
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/search')
def search():
    """البحث العام في النظام"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return render_template('search_results.html', 
                             query=query, 
                             employees=[], 
                             events=[])
    
    try:
        # البحث في الموظفين
        employee_results = employee_service.get_all_employees(
            search=query, per_page=10
        )
        
        # البحث في الأحداث
        event_results = professional_event_service.get_all_events(
            search=query, per_page=10
        )
        
        return render_template('search_results.html',
                             query=query,
                             employees=employee_results['employees'],
                             events=event_results['events'])
    except Exception as e:
        return render_template('errors/500.html', error=str(e)), 500

