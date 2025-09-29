from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, date
from ..services import employee_service, professional_event_service
from ..models import EventType
from ..calculation_engine import calculation_engine

event_bp = Blueprint('events', __name__)

@event_bp.route('/')
def list_events():
    """عرض قائمة الأحداث المهنية"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    event_type = request.args.get('event_type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    sort_by = request.args.get('sort_by', 'event_date')
    
    try:
        # تحويل التواريخ
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date() if date_from else None
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date() if date_to else None
        event_type_obj = EventType(event_type) if event_type else None
        
        result = professional_event_service.get_all_events(
            page=page,
            per_page=12,
            search=search,
            event_type=event_type_obj,
            date_from=date_from_obj,
            date_to=date_to_obj,
            sort_by=sort_by
        )
        
        # الحصول على الإحصائيات
        stats = professional_event_service.get_events_statistics()
        
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
        
        return render_template('events/list.html',
                             events=result['events'],
                             pagination=result,
                             stats=stats,
                             search=search,
                             event_type=event_type,
                             date_from=date_from,
                             date_to=date_to,
                             sort_by=sort_by,
                             event_types=event_types)
    except Exception as e:
        flash(f'حدث خطأ في تحميل الأحداث: {str(e)}', 'error')
        return render_template('events/list.html', events=[], pagination={}, stats={})

@event_bp.route('/add', methods=['GET', 'POST'])
@event_bp.route('/add/<int:employee_id>', methods=['GET', 'POST'])
def add_event(employee_id=None):
    """إضافة حدث مهني جديد"""
    if request.method == 'POST':
        try:
            # الحصول على البيانات الأساسية
            selected_employees = request.form.getlist('employee_ids')
            if not selected_employees:
                flash('يرجى تحديد موظف واحد على الأقل', 'error')
                return render_template('events/add.html')
            
            event_type = EventType(request.form['event_type'])
            event_date = datetime.strptime(request.form['event_date'], '%Y-%m-%d').date()
            description = request.form.get('description', '').strip()
            document_number = request.form.get('document_number', '').strip()
            document_date = None
            if request.form.get('document_date'):
                document_date = datetime.strptime(request.form['document_date'], '%Y-%m-%d').date()
            
            # معالجة البيانات الخاصة بكل نوع حدث
            event_data = {
                'event_type': event_type.value,
                'event_date': event_date,
                'description': description,
                'document_number': document_number,
                'document_date': document_date
            }
            
            # كتاب الشكر
            if event_type == EventType.COMMENDATION:
                reduction_months = int(request.form.get('reduction_months', 0))
                if reduction_months == 0:
                    flash('يرجى تحديد مدة التقليص لكتاب الشكر', 'error')
                    return render_template('events/add.html')
                event_data['reduction_months'] = reduction_months
            
            # الشهادة الأعلى
            elif event_type == EventType.HIGHER_DEGREE:
                event_data['new_job_category'] = request.form.get('new_job_category', '')
                event_data['new_job_title'] = request.form.get('new_job_title', '')
                event_data['new_academic_degree'] = request.form.get('new_academic_degree', '')
            
            # الإجازات
            elif event_type in [EventType.UNPAID_LEAVE, EventType.DISABILITY_LEAVE, 
                               EventType.FIVE_YEAR_LEAVE, EventType.MATERNITY_LEAVE]:
                start_date = datetime.strptime(request.form['leave_start_date'], '%Y-%m-%d').date()
                end_date = datetime.strptime(request.form['leave_end_date'], '%Y-%m-%d').date()
                
                if end_date <= start_date:
                    flash('تاريخ نهاية الإجازة يجب أن يكون بعد تاريخ البداية', 'error')
                    return render_template('events/add.html')
                
                event_data['start_date'] = start_date
                event_data['end_date'] = end_date
            
            # الحدث المخصص
            elif event_type == EventType.CUSTOM:
                adjustment_type = request.form.get('custom_adjustment_type', '')
                months = int(request.form.get('custom_months', 0))
                notes = request.form.get('custom_notes', '').strip()
                
                if not notes:
                    flash('الملاحظات إلزامية للأحداث المخصصة', 'error')
                    return render_template('events/add.html')
                
                if months == 0:
                    flash('يرجى تحديد عدد الشهور للحدث المخصص', 'error')
                    return render_template('events/add.html')
                
                event_data['adjustment_type'] = adjustment_type
                event_data['months'] = months
                event_data['notes'] = notes
            
            # إنشاء الأحداث للموظفين المحددين
            created_events = []
            for emp_id in selected_employees:
                event_data['employee_id'] = int(emp_id)
                try:
                    event = professional_event_service.create_event(event_data.copy())
                    created_events.append(event)
                    
                    # تحديث بيانات الموظف للشهادة الأعلى
                    if event_type == EventType.HIGHER_DEGREE:
                        employee = employee_service.get_employee_by_id(int(emp_id))
                        if employee:
                            update_data = {}
                            if event_data.get('new_job_category'):
                                update_data['job_category'] = event_data['new_job_category']
                            if event_data.get('new_job_title'):
                                update_data['title'] = event_data['new_job_title']
                            if event_data.get('new_academic_degree'):
                                update_data['academic_degree'] = event_data['new_academic_degree']
                            
                            if update_data:
                                employee_service.update_employee(int(emp_id), update_data)
                
                except ValueError as e:
                    flash(f'خطأ للموظف {emp_id}: {str(e)}', 'error')
                    continue
            
            if created_events:
                flash(f'تم إضافة الحدث المهني بنجاح لـ {len(created_events)} موظف!', 'success')
                return redirect(url_for('events.list_events'))
            else:
                flash('فشل في إضافة الحدث المهني', 'error')
                
        except Exception as e:
            flash(f'حدث خطأ أثناء إضافة الحدث: {str(e)}', 'error')
    
    # الحصول على قائمة الموظفين
    try:
        employees_result = employee_service.get_all_employees(per_page=1000)
        employees = employees_result['employees']
        
        # تجميع الموظفين حسب الصنف
        employees_by_category = {}
        for emp in employees:
            if emp.job_category not in employees_by_category:
                employees_by_category[emp.job_category] = []
            employees_by_category[emp.job_category].append(emp)
        
        selected_employee = None
        if employee_id:
            selected_employee = employee_service.get_employee_by_id(employee_id)
        
        return render_template('events/add.html',
                             employees_by_category=employees_by_category,
                             selected_employee=selected_employee)
    except Exception as e:
        flash(f'حدث خطأ في تحميل الموظفين: {str(e)}', 'error')
        return render_template('events/add.html', employees_by_category={})

@event_bp.route('/<int:event_id>')
def view_event(event_id):
    """عرض تفاصيل حدث مهني"""
    try:
        event = professional_event_service.get_event_by_id(event_id)
        if not event:
            flash('الحدث المهني غير موجود', 'error')
            return redirect(url_for('events.list_events'))
        
        return render_template('events/view.html', event=event)
    except Exception as e:
        flash(f'حدث خطأ في تحميل الحدث: {str(e)}', 'error')
        return redirect(url_for('events.list_events'))

@event_bp.route('/<int:event_id>/edit', methods=['GET', 'POST'])
def edit_event(event_id):
    """تعديل حدث مهني"""
    try:
        event = professional_event_service.get_event_by_id(event_id)
        if not event:
            flash('الحدث المهني غير موجود', 'error')
            return redirect(url_for('events.list_events'))
        
        if request.method == 'POST':
            data = {
                'event_date': datetime.strptime(request.form['event_date'], '%Y-%m-%d').date(),
                'description': request.form.get('description', '').strip(),
                'document_number': request.form.get('document_number', '').strip(),
                'notes': request.form.get('notes', '').strip()
            }
            
            if request.form.get('document_date'):
                data['document_date'] = datetime.strptime(request.form['document_date'], '%Y-%m-%d').date()
            
            updated_event = professional_event_service.update_event(event_id, data)
            if updated_event:
                flash('تم تحديث الحدث المهني بنجاح!', 'success')
                return redirect(url_for('events.view_event', event_id=event_id))
            else:
                flash('فشل في تحديث الحدث المهني', 'error')
        
        return render_template('events/edit.html', event=event)
    except Exception as e:
        flash(f'حدث خطأ: {str(e)}', 'error')
        return redirect(url_for('events.list_events'))

@event_bp.route('/<int:event_id>/delete', methods=['POST'])
def delete_event(event_id):
    """حذف حدث مهني"""
    try:
        event = professional_event_service.get_event_by_id(event_id)
        if not event:
            flash('الحدث المهني غير موجود', 'error')
            return redirect(url_for('events.list_events'))
        
        event_description = event.event_type_name
        if professional_event_service.delete_event(event_id):
            flash(f'تم حذف الحدث "{event_description}" بنجاح', 'success')
        else:
            flash('فشل في حذف الحدث المهني', 'error')
            
    except Exception as e:
        flash(f'حدث خطأ أثناء حذف الحدث: {str(e)}', 'error')
    
    return redirect(url_for('events.list_events'))

@event_bp.route('/api/statistics')
def api_statistics():
    """API للحصول على إحصائيات الأحداث"""
    try:
        stats = professional_event_service.get_events_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@event_bp.route('/api/validate', methods=['POST'])
def api_validate_event():
    """API للتحقق من صحة الحدث المهني"""
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        event_type = EventType(data.get('event_type'))
        event_date = datetime.strptime(data.get('event_date'), '%Y-%m-%d').date()
        
        employee = employee_service.get_employee_by_id(employee_id)
        if not employee:
            return jsonify({'valid': False, 'message': 'الموظف غير موجود'})
        
        is_valid, error_message = calculation_engine.validate_professional_event(
            employee, event_type, event_date, **data
        )
        
        return jsonify({
            'valid': is_valid,
            'message': error_message if not is_valid else 'الحدث صحيح'
        })
    except Exception as e:
        return jsonify({'valid': False, 'message': str(e)})

