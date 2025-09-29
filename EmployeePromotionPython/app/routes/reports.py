from flask import Blueprint, render_template, request, jsonify, make_response, send_file
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import json
import io
import csv
from ..services import employee_service, professional_event_service, promotion_history_service
from ..models import EventType, PromotionType

report_bp = Blueprint('reports', __name__)

@report_bp.route('/')
def dashboard():
    """لوحة تحكم التقارير والإحصائيات"""
    try:
        # الحصول على الإحصائيات الأساسية
        employee_stats = employee_service.get_employees_statistics()
        event_stats = professional_event_service.get_events_statistics()
        promotion_stats = promotion_history_service.get_promotion_statistics()
        
        # إحصائيات متقدمة
        advanced_stats = _get_advanced_statistics()
        
        return render_template('reports/dashboard.html',
                             employee_stats=employee_stats,
                             event_stats=event_stats,
                             promotion_stats=promotion_stats,
                             advanced_stats=advanced_stats)
    except Exception as e:
        return render_template('errors/500.html', error=str(e)), 500

@report_bp.route('/employees')
def employees_report():
    """تقرير الموظفين المفصل"""
    # فلاتر التقرير
    job_category = request.args.get('job_category', '')
    job_grade = request.args.get('job_grade', type=int)
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    report_type = request.args.get('report_type', 'summary')
    
    try:
        # تحويل التواريخ
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date() if date_from else None
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else None
        
        # الحصول على بيانات الموظفين
        employees_result = employee_service.get_all_employees(
            per_page=1000,
            job_category=job_category,
            job_grade=job_grade
        )
        
        employees = employees_result['employees']
        
        # فلترة حسب تاريخ التعيين
        if date_from_obj or date_to_obj:
            filtered_employees = []
            for emp in employees:
                if date_from_obj and emp.start_date < date_from_obj:
                    continue
                if date_to_obj and emp.start_date > date_to_obj:
                    continue
                filtered_employees.append(emp)
            employees = filtered_employees
        
        # إعداد البيانات للتقرير
        report_data = _prepare_employees_report_data(employees, report_type)
        
        # قوائم الفلاتر
        categories = ['تدريسي', 'إداري', 'فني', 'خدمي']
        grades = list(range(1, 11))
        
        return render_template('reports/employees.html',
                             employees=employees,
                             report_data=report_data,
                             job_category=job_category,
                             job_grade=job_grade,
                             date_from=date_from,
                             date_to=date_to,
                             report_type=report_type,
                             categories=categories,
                             grades=grades)
    except Exception as e:
        return render_template('errors/500.html', error=str(e)), 500

@report_bp.route('/events')
def events_report():
    """تقرير الأحداث المهنية المفصل"""
    # فلاتر التقرير
    event_type = request.args.get('event_type', '')
    employee_id = request.args.get('employee_id', type=int)
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    report_type = request.args.get('report_type', 'summary')
    
    try:
        # تحويل التواريخ
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date() if date_from else None
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else None
        event_type_obj = EventType(event_type) if event_type else None
        
        # الحصول على بيانات الأحداث
        events_result = professional_event_service.get_all_events(
            per_page=1000,
            event_type=event_type_obj,
            employee_id=employee_id,
            date_from=date_from_obj,
            date_to=date_to_obj
        )
        
        events = events_result['events']
        
        # إعداد البيانات للتقرير
        report_data = _prepare_events_report_data(events, report_type)
        
        # قائمة أنواع الأحداث
        event_types = [
            ('commendation', 'كتاب شكر وتقدير'),
            ('higher_degree', 'شهادة أعلى'),
            ('notice_penalty', 'عقوبة لفت نظر'),
            ('warning_penalty', 'عقوبة إنذار'),
            ('reprimand_penalty', 'عقوبة توبيخ'),
            ('unpaid_leave', 'إجازة بدون راتب'),
            ('disability_leave', 'إجازة رعاية المعاقين'),
            ('five_year_leave', 'إجازة الخمس سنوات'),
            ('maternity_leave', 'إجازة أمومة'),
            ('custom', 'حدث مخصص')
        ]
        
        return render_template('reports/events.html',
                             events=events,
                             report_data=report_data,
                             event_type=event_type,
                             employee_id=employee_id,
                             date_from=date_from,
                             date_to=date_to,
                             report_type=report_type,
                             event_types=event_types)
    except Exception as e:
        return render_template('errors/500.html', error=str(e)), 500

@report_bp.route('/promotions')
def promotions_report():
    """تقرير الترفيعات والعلاوات المفصل"""
    # فلاتر التقرير
    promotion_type = request.args.get('promotion_type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    report_type = request.args.get('report_type', 'summary')
    
    try:
        # تحويل التواريخ
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date() if date_from else None
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else None
        promotion_type_obj = PromotionType(promotion_type) if promotion_type else None
        
        # الحصول على بيانات الترفيعات
        promotions_result = promotion_history_service.get_all_promotions(
            per_page=1000,
            promotion_type=promotion_type_obj,
            date_from=date_from_obj,
            date_to=date_to_obj
        )
        
        promotions = promotions_result['promotions']
        
        # إعداد البيانات للتقرير
        report_data = _prepare_promotions_report_data(promotions, report_type)
        
        return render_template('reports/promotions.html',
                             promotions=promotions,
                             report_data=report_data,
                             promotion_type=promotion_type,
                             date_from=date_from,
                             date_to=date_to,
                             report_type=report_type)
    except Exception as e:
        return render_template('errors/500.html', error=str(e)), 500

@report_bp.route('/upcoming-entitlements')
def upcoming_entitlements():
    """تقرير الاستحقاقات القادمة"""
    days_ahead = request.args.get('days_ahead', 30, type=int)
    job_category = request.args.get('job_category', '')
    entitlement_type = request.args.get('entitlement_type', '')
    
    try:
        # الحصول على جميع الموظفين
        employees_result = employee_service.get_all_employees(
            per_page=1000,
            job_category=job_category
        )
        
        employees = employees_result['employees']
        
        # حساب الاستحقاقات القادمة
        upcoming = []
        today = date.today()
        target_date = today + timedelta(days=days_ahead)
        
        for emp in employees:
            next_date = emp.next_entitlement_date
            next_type = emp.next_entitlement_type
            
            if next_date and next_date <= target_date:
                if entitlement_type and next_type != entitlement_type:
                    continue
                
                days_remaining = (next_date - today).days
                upcoming.append({
                    'employee': emp,
                    'type': next_type,
                    'date': next_date,
                    'days_remaining': days_remaining,
                    'is_overdue': days_remaining < 0,
                    'is_urgent': 0 <= days_remaining <= 7
                })
        
        # ترتيب حسب التاريخ
        upcoming.sort(key=lambda x: x['date'])
        
        # إحصائيات
        stats = {
            'total': len(upcoming),
            'overdue': len([u for u in upcoming if u['is_overdue']]),
            'urgent': len([u for u in upcoming if u['is_urgent']]),
            'allowances': len([u for u in upcoming if u['type'] == 'علاوة']),
            'promotions': len([u for u in upcoming if u['type'] == 'ترفيع'])
        }
        
        categories = ['تدريسي', 'إداري', 'فني', 'خدمي']
        
        return render_template('reports/upcoming_entitlements.html',
                             upcoming=upcoming,
                             stats=stats,
                             days_ahead=days_ahead,
                             job_category=job_category,
                             entitlement_type=entitlement_type,
                             categories=categories)
    except Exception as e:
        return render_template('errors/500.html', error=str(e)), 500

@report_bp.route('/api/charts/employees-by-category')
def api_employees_by_category():
    """API للرسم البياني - الموظفين حسب الصنف"""
    try:
        stats = employee_service.get_employees_statistics()
        
        labels = [stat['category'] for stat in stats['category_stats']]
        data = [stat['count'] for stat in stats['category_stats']]
        
        return jsonify({
            'labels': labels,
            'datasets': [{
                'label': 'عدد الموظفين',
                'data': data,
                'backgroundColor': [
                    '#667eea', '#764ba2', '#f093fb', '#f5576c'
                ]
            }]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@report_bp.route('/api/charts/employees-by-grade')
def api_employees_by_grade():
    """API للرسم البياني - الموظفين حسب الدرجة"""
    try:
        stats = employee_service.get_employees_statistics()
        
        labels = [f'الدرجة {stat["grade"]}' for stat in stats['grade_stats']]
        data = [stat['count'] for stat in stats['grade_stats']]
        
        return jsonify({
            'labels': labels,
            'datasets': [{
                'label': 'عدد الموظفين',
                'data': data,
                'backgroundColor': '#667eea',
                'borderColor': '#764ba2',
                'borderWidth': 1
            }]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@report_bp.route('/api/charts/events-by-type')
def api_events_by_type():
    """API للرسم البياني - الأحداث حسب النوع"""
    try:
        stats = professional_event_service.get_events_statistics()
        
        # ترجمة أنواع الأحداث
        type_names = {
            'commendation': 'كتب الشكر',
            'higher_degree': 'الشهادات',
            'notice_penalty': 'لفت نظر',
            'warning_penalty': 'إنذار',
            'reprimand_penalty': 'توبيخ',
            'unpaid_leave': 'إجازة بدون راتب',
            'disability_leave': 'إجازة رعاية معاقين',
            'five_year_leave': 'إجازة خمس سنوات',
            'maternity_leave': 'إجازة أمومة',
            'custom': 'أحداث مخصصة'
        }
        
        labels = [type_names.get(stat['type'], stat['type']) for stat in stats['type_stats']]
        data = [stat['count'] for stat in stats['type_stats']]
        
        return jsonify({
            'labels': labels,
            'datasets': [{
                'label': 'عدد الأحداث',
                'data': data,
                'backgroundColor': [
                    '#28a745', '#17a2b8', '#dc3545', '#ffc107',
                    '#6f42c1', '#e83e8c', '#20c997', '#fd7e14'
                ]
            }]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@report_bp.route('/api/charts/promotions-monthly')
def api_promotions_monthly():
    """API للرسم البياني - الترفيعات الشهرية"""
    try:
        stats = promotion_history_service.get_promotion_statistics()
        
        labels = [stat['month'] for stat in stats['monthly_stats']]
        data = [stat['count'] for stat in stats['monthly_stats']]
        
        return jsonify({
            'labels': labels,
            'datasets': [{
                'label': 'عدد الترفيعات والعلاوات',
                'data': data,
                'backgroundColor': 'rgba(102, 126, 234, 0.2)',
                'borderColor': '#667eea',
                'borderWidth': 2,
                'fill': True
            }]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@report_bp.route('/export/employees')
def export_employees():
    """تصدير تقرير الموظفين إلى CSV"""
    try:
        employees_result = employee_service.get_all_employees(per_page=1000)
        employees = employees_result['employees']
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # كتابة الرأس
        writer.writerow([
            'الاسم الكامل', 'الصنف الوظيفي', 'الدرجة', 'المرحلة',
            'تاريخ التعيين', 'الخدمة الفعلية', 'الاستحقاق القادم', 'تاريخ الاستحقاق'
        ])
        
        # كتابة البيانات
        for emp in employees:
            writer.writerow([
                emp.full_name,
                emp.job_category,
                emp.job_grade,
                emp.job_stage,
                emp.start_date.strftime('%Y-%m-%d'),
                emp.actual_service_formatted,
                emp.next_entitlement_type,
                emp.next_entitlement_date.strftime('%Y-%m-%d') if emp.next_entitlement_date else ''
            ])
        
        output.seek(0)
        
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=employees_report_{date.today()}.csv'
        
        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _get_advanced_statistics():
    """الحصول على إحصائيات متقدمة"""
    try:
        # إحصائيات الاستحقاقات القادمة
        employees_result = employee_service.get_all_employees(per_page=1000)
        employees = employees_result['employees']
        
        today = date.today()
        upcoming_30 = 0
        upcoming_60 = 0
        upcoming_90 = 0
        overdue = 0
        
        for emp in employees:
            next_date = emp.next_entitlement_date
            if next_date:
                days_diff = (next_date - today).days
                if days_diff < 0:
                    overdue += 1
                elif days_diff <= 30:
                    upcoming_30 += 1
                elif days_diff <= 60:
                    upcoming_60 += 1
                elif days_diff <= 90:
                    upcoming_90 += 1
        
        return {
            'upcoming_30': upcoming_30,
            'upcoming_60': upcoming_60,
            'upcoming_90': upcoming_90,
            'overdue': overdue
        }
    except:
        return {}

def _prepare_employees_report_data(employees, report_type):
    """إعداد بيانات تقرير الموظفين"""
    if report_type == 'summary':
        return {
            'total_employees': len(employees),
            'by_category': _group_by_field(employees, 'job_category'),
            'by_grade': _group_by_field(employees, 'job_grade'),
            'avg_service_years': sum(emp.actual_service_years for emp in employees) / len(employees) if employees else 0
        }
    return {}

def _prepare_events_report_data(events, report_type):
    """إعداد بيانات تقرير الأحداث"""
    if report_type == 'summary':
        return {
            'total_events': len(events),
            'by_type': _group_by_field(events, 'event_type'),
            'positive_events': len([e for e in events if e.event_category == 'positive']),
            'negative_events': len([e for e in events if e.event_category == 'negative'])
        }
    return {}

def _prepare_promotions_report_data(promotions, report_type):
    """إعداد بيانات تقرير الترفيعات"""
    if report_type == 'summary':
        return {
            'total_promotions': len(promotions),
            'by_type': _group_by_field(promotions, 'promotion_type'),
            'recent_promotions': len([p for p in promotions if (date.today() - p.effective_date).days <= 30])
        }
    return {}

def _group_by_field(items, field):
    """تجميع العناصر حسب حقل معين"""
    groups = {}
    for item in items:
        value = getattr(item, field)
        if hasattr(value, 'value'):  # للـ Enums
            value = value.value
        if value not in groups:
            groups[value] = 0
        groups[value] += 1
    return groups

