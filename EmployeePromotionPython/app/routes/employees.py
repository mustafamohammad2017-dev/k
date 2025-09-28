from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, date
from ..services import employee_service, professional_event_service, promotion_history_service
from ..models import Employee, EventType
from ..calculation_engine import calculation_engine

employee_bp = Blueprint('employees', __name__)

@employee_bp.route('/')
def list_employees():
    """عرض قائمة الموظفين"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    job_category = request.args.get('job_category', '')
    job_grade = request.args.get('job_grade', type=int)
    sort_by = request.args.get('sort_by', 'full_name')
    
    try:
        result = employee_service.get_all_employees(
            page=page,
            per_page=12,
            search=search,
            job_category=job_category,
            job_grade=job_grade,
            sort_by=sort_by
        )
        
        # قائمة الأصناف للفلترة
        categories = ['تدريسي', 'إداري', 'فني', 'خدمي']
        grades = list(range(1, 11))
        
        return render_template('employees/list.html',
                             employees=result['employees'],
                             pagination=result,
                             search=search,
                             job_category=job_category,
                             job_grade=job_grade,
                             sort_by=sort_by,
                             categories=categories,
                             grades=grades)
    except Exception as e:
        flash(f'حدث خطأ في تحميل الموظفين: {str(e)}', 'error')
        return render_template('employees/list.html', employees=[], pagination={})

@employee_bp.route('/add', methods=['GET', 'POST'])
def add_employee():
    """إضافة موظف جديد"""
    if request.method == 'POST':
        try:
            data = {
                'full_name': request.form['full_name'].strip(),
                'title': request.form.get('title', '').strip(),
                'job_category': request.form['job_category'],
                'academic_degree': request.form.get('academic_degree', ''),
                'job_grade': int(request.form['job_grade']),
                'job_stage': int(request.form['job_stage']),
                'job_title_number': int(request.form['job_title_number']) if request.form.get('job_title_number') else None,
                'allowance_tracker': request.form['allowance_tracker'],
                'start_date': datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
                'last_allowance_date': datetime.strptime(request.form['last_allowance_date'], '%Y-%m-%d').date(),
                'last_promotion_date': datetime.strptime(request.form['last_promotion_date'], '%Y-%m-%d').date()
            }
            
            # التحقق من صحة البيانات
            if not data['full_name']:
                flash('اسم الموظف مطلوب', 'error')
                return render_template('employees/add.html')
            
            if data['job_grade'] < 1 or data['job_grade'] > 10:
                flash('الدرجة الوظيفية يجب أن تكون بين 1 و 10', 'error')
                return render_template('employees/add.html')
            
            if data['job_stage'] < 1 or data['job_stage'] > 11:
                flash('المرحلة الوظيفية يجب أن تكون بين 1 و 11', 'error')
                return render_template('employees/add.html')
            
            # إنشاء الموظف
            employee = employee_service.create_employee(data)
            flash(f'تم إضافة الموظف {employee.full_name} بنجاح!', 'success')
            return redirect(url_for('employees.view_employee', employee_id=employee.id))
            
        except ValueError as e:
            flash(f'خطأ في البيانات: {str(e)}', 'error')
        except Exception as e:
            flash(f'حدث خطأ أثناء إضافة الموظف: {str(e)}', 'error')
    
    return render_template('employees/add.html')

@employee_bp.route('/<int:employee_id>')
def view_employee(employee_id):
    """عرض ملف الموظف"""
    try:
        employee = employee_service.get_employee_by_id(employee_id)
        if not employee:
            flash('الموظف غير موجود', 'error')
            return redirect(url_for('employees.list_employees'))
        
        # معالجة الاستحقاقات التلقائية
        calculation_engine.process_employee_entitlements(employee)
        
        # الحصول على السجلات
        promotion_history = promotion_history_service.get_employee_promotion_history(employee_id)
        professional_events = professional_event_service.get_all_events(
            employee_id=employee_id, per_page=50
        )['events']
        
        # حساب الأيام المتبقية للاستحقاق القادم
        next_date = employee.next_entitlement_date
        days_remaining = (next_date - date.today()).days if next_date else 0
        
        return render_template('employees/profile.html',
                             employee=employee,
                             promotion_history=promotion_history,
                             professional_events=professional_events,
                             days_remaining=days_remaining)
    except Exception as e:
        flash(f'حدث خطأ في تحميل ملف الموظف: {str(e)}', 'error')
        return redirect(url_for('employees.list_employees'))

@employee_bp.route('/<int:employee_id>/edit', methods=['GET', 'POST'])
def edit_employee(employee_id):
    """تعديل بيانات الموظف"""
    try:
        employee = employee_service.get_employee_by_id(employee_id)
        if not employee:
            flash('الموظف غير موجود', 'error')
            return redirect(url_for('employees.list_employees'))
        
        if request.method == 'POST':
            data = {
                'full_name': request.form['full_name'].strip(),
                'title': request.form.get('title', '').strip(),
                'job_category': request.form['job_category'],
                'academic_degree': request.form.get('academic_degree', ''),
                'job_grade': int(request.form['job_grade']),
                'job_stage': int(request.form['job_stage']),
                'job_title_number': int(request.form['job_title_number']) if request.form.get('job_title_number') else None,
                'allowance_tracker': request.form['allowance_tracker'],
                'start_date': datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
                'last_allowance_date': datetime.strptime(request.form['last_allowance_date'], '%Y-%m-%d').date(),
                'last_promotion_date': datetime.strptime(request.form['last_promotion_date'], '%Y-%m-%d').date()
            }
            
            # تحديث الموظف
            updated_employee = employee_service.update_employee(employee_id, data)
            if updated_employee:
                flash(f'تم تحديث بيانات الموظف {updated_employee.full_name} بنجاح!', 'success')
                return redirect(url_for('employees.view_employee', employee_id=employee_id))
            else:
                flash('فشل في تحديث بيانات الموظف', 'error')
        
        return render_template('employees/edit.html', employee=employee)
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'error')
        return redirect(url_for('employees.list_employees'))

@employee_bp.route('/<int:employee_id>/delete', methods=['POST'])
def delete_employee(employee_id):
    """حذف موظف"""
    try:
        employee = employee_service.get_employee_by_id(employee_id)
        if not employee:
            flash('الموظف غير موجود', 'error')
            return redirect(url_for('employees.list_employees'))
        
        employee_name = employee.full_name
        if employee_service.delete_employee(employee_id):
            flash(f'تم حذف الموظف {employee_name} بنجاح', 'success')
        else:
            flash('فشل في حذف الموظف', 'error')
            
    except Exception as e:
        flash(f'حدث خطأ أثناء حذف الموظف: {str(e)}', 'error')
    
    return redirect(url_for('employees.list_employees'))

@employee_bp.route('/api/statistics')
def api_statistics():
    """API للحصول على إحصائيات الموظفين"""
    try:
        stats = employee_service.get_employees_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@employee_bp.route('/api/search')
def api_search():
    """API للبحث في الموظفين"""
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)
    
    try:
        if not query:
            return jsonify([])
        
        result = employee_service.get_all_employees(
            search=query, per_page=limit
        )
        
        employees_data = []
        for emp in result['employees']:
            employees_data.append({
                'id': emp.id,
                'full_name': emp.full_name,
                'job_category': emp.job_category,
                'job_grade': emp.job_grade,
                'job_stage': emp.job_stage
            })
        
        return jsonify(employees_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

