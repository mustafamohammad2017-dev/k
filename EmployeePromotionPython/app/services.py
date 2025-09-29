from typing import List, Optional, Dict, Any
from datetime import date, datetime
from sqlalchemy import and_, or_, extract, func, desc, asc
from sqlalchemy.orm import joinedload
from .models import db, Employee, ProfessionalEvent, PromotionHistory, EventType, PromotionType
from .calculation_engine import calculation_engine

class EmployeeService:
    """خدمة إدارة الموظفين"""
    
    @staticmethod
    def get_all_employees(page: int = 1, per_page: int = 20, 
                         search: str = None, job_category: str = None,
                         job_grade: int = None, sort_by: str = 'full_name') -> Dict[str, Any]:
        """
        الحصول على جميع الموظفين مع الفلترة والترقيم
        
        Args:
            page: رقم الصفحة
            per_page: عدد الموظفين في الصفحة
            search: نص البحث
            job_category: صنف الوظيفة
            job_grade: الدرجة الوظيفية
            sort_by: ترتيب النتائج
            
        Returns:
            قاموس يحتوي على الموظفين ومعلومات الترقيم
        """
        query = Employee.query
        
        # تطبيق الفلاتر
        if search:
            query = query.filter(
                or_(
                    Employee.full_name.contains(search),
                    Employee.title.contains(search),
                    Employee.academic_degree.contains(search)
                )
            )
        
        if job_category:
            query = query.filter(Employee.job_category == job_category)
        
        if job_grade:
            query = query.filter(Employee.job_grade == job_grade)
        
        # تطبيق الترتيب
        if sort_by == 'full_name':
            query = query.order_by(Employee.full_name)
        elif sort_by == 'start_date':
            query = query.order_by(desc(Employee.start_date))
        elif sort_by == 'job_grade':
            query = query.order_by(Employee.job_grade, Employee.job_stage)
        elif sort_by == 'job_category':
            query = query.order_by(Employee.job_category, Employee.full_name)
        
        # تطبيق الترقيم
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return {
            'employees': pagination.items,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'prev_num': pagination.prev_num,
            'next_num': pagination.next_num
        }
    
    @staticmethod
    def get_employee_by_id(employee_id: int) -> Optional[Employee]:
        """الحصول على موظف بالمعرف"""
        return Employee.query.options(
            joinedload(Employee.professional_events),
            joinedload(Employee.promotion_history)
        ).get(employee_id)
    
    @staticmethod
    def create_employee(data: Dict[str, Any]) -> Employee:
        """إنشاء موظف جديد"""
        employee = Employee(
            full_name=data['full_name'],
            title=data.get('title', ''),
            job_category=data['job_category'],
            academic_degree=data.get('academic_degree', ''),
            job_grade=data['job_grade'],
            job_stage=data['job_stage'],
            job_title_number=data.get('job_title_number'),
            allowance_tracker=data['allowance_tracker'],
            start_date=data['start_date'],
            last_allowance_date=data['last_allowance_date'],
            last_promotion_date=data['last_promotion_date'],
            photo_path=data.get('photo_path')
        )
        
        db.session.add(employee)
        db.session.commit()
        
        # معالجة الاستحقاقات التلقائية
        calculation_engine.process_employee_entitlements(employee)
        
        return employee
    
    @staticmethod
    def update_employee(employee_id: int, data: Dict[str, Any]) -> Optional[Employee]:
        """تحديث بيانات موظف"""
        employee = Employee.query.get(employee_id)
        if not employee:
            return None
        
        # تحديث البيانات
        for key, value in data.items():
            if hasattr(employee, key):
                setattr(employee, key, value)
        
        employee.updated_at = datetime.utcnow()
        db.session.commit()
        
        return employee
    
    @staticmethod
    def delete_employee(employee_id: int) -> bool:
        """حذف موظف"""
        employee = Employee.query.get(employee_id)
        if not employee:
            return False
        
        db.session.delete(employee)
        db.session.commit()
        return True
    
    @staticmethod
    def get_employees_statistics() -> Dict[str, Any]:
        """الحصول على إحصائيات الموظفين"""
        total_employees = Employee.query.count()
        
        # إحصائيات حسب الصنف
        category_stats = db.session.query(
            Employee.job_category,
            func.count(Employee.id).label('count')
        ).group_by(Employee.job_category).all()
        
        # إحصائيات حسب الدرجة
        grade_stats = db.session.query(
            Employee.job_grade,
            func.count(Employee.id).label('count')
        ).group_by(Employee.job_grade).order_by(Employee.job_grade).all()
        
        # الاستحقاقات القادمة (خلال 30 يوم)
        upcoming_entitlements = []
        employees = Employee.query.all()
        for emp in employees:
            next_date = emp.next_entitlement_date
            if next_date and (next_date - date.today()).days <= 30:
                upcoming_entitlements.append({
                    'employee': emp,
                    'type': emp.next_entitlement_type,
                    'date': next_date,
                    'days_remaining': (next_date - date.today()).days
                })
        
        return {
            'total_employees': total_employees,
            'category_stats': [{'category': cat, 'count': count} for cat, count in category_stats],
            'grade_stats': [{'grade': grade, 'count': count} for grade, count in grade_stats],
            'upcoming_entitlements': upcoming_entitlements
        }

class ProfessionalEventService:
    """خدمة إدارة الأحداث المهنية"""
    
    @staticmethod
    def get_all_events(page: int = 1, per_page: int = 20,
                      search: str = None, event_type: EventType = None,
                      employee_id: int = None, date_from: date = None,
                      date_to: date = None, sort_by: str = 'event_date') -> Dict[str, Any]:
        """
        الحصول على جميع الأحداث المهنية مع الفلترة
        
        Args:
            page: رقم الصفحة
            per_page: عدد الأحداث في الصفحة
            search: نص البحث
            event_type: نوع الحدث
            employee_id: معرف الموظف
            date_from: من تاريخ
            date_to: إلى تاريخ
            sort_by: ترتيب النتائج
            
        Returns:
            قاموس يحتوي على الأحداث ومعلومات الترقيم
        """
        query = ProfessionalEvent.query.options(joinedload(ProfessionalEvent.employee))
        
        # تطبيق الفلاتر
        if search:
            query = query.join(Employee).filter(
                or_(
                    Employee.full_name.contains(search),
                    ProfessionalEvent.description.contains(search),
                    ProfessionalEvent.document_number.contains(search)
                )
            )
        
        if event_type:
            query = query.filter(ProfessionalEvent.event_type == event_type)
        
        if employee_id:
            query = query.filter(ProfessionalEvent.employee_id == employee_id)
        
        if date_from:
            query = query.filter(ProfessionalEvent.event_date >= date_from)
        
        if date_to:
            query = query.filter(ProfessionalEvent.event_date <= date_to)
        
        # تطبيق الترتيب
        if sort_by == 'event_date':
            query = query.order_by(desc(ProfessionalEvent.event_date))
        elif sort_by == 'employee':
            query = query.join(Employee).order_by(Employee.full_name)
        elif sort_by == 'event_type':
            query = query.order_by(ProfessionalEvent.event_type)
        
        # تطبيق الترقيم
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return {
            'events': pagination.items,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'prev_num': pagination.prev_num,
            'next_num': pagination.next_num
        }
    
    @staticmethod
    def get_event_by_id(event_id: int) -> Optional[ProfessionalEvent]:
        """الحصول على حدث مهني بالمعرف"""
        return ProfessionalEvent.query.options(
            joinedload(ProfessionalEvent.employee)
        ).get(event_id)
    
    @staticmethod
    def create_event(data: Dict[str, Any]) -> ProfessionalEvent:
        """إنشاء حدث مهني جديد"""
        # التحقق من صحة الحدث
        employee = Employee.query.get(data['employee_id'])
        if not employee:
            raise ValueError("الموظف غير موجود")
        
        event_type = EventType(data['event_type'])
        is_valid, error_message = calculation_engine.validate_professional_event(
            employee, event_type, data['event_date'], **data
        )
        
        if not is_valid:
            raise ValueError(error_message)
        
        # حساب التأثير
        impact_months = calculation_engine.calculate_event_impact(event_type, **data)
        
        # إنشاء الحدث
        event = ProfessionalEvent(
            employee_id=data['employee_id'],
            event_type=event_type,
            event_date=data['event_date'],
            description=data.get('description', ''),
            document_number=data.get('document_number'),
            document_date=data.get('document_date'),
            impact_months=impact_months,
            start_date=data.get('start_date'),
            end_date=data.get('end_date'),
            notes=data.get('notes', '')
        )
        
        db.session.add(event)
        db.session.commit()
        
        # إعادة معالجة استحقاقات الموظف
        calculation_engine.process_employee_entitlements(employee)
        
        return event
    
    @staticmethod
    def update_event(event_id: int, data: Dict[str, Any]) -> Optional[ProfessionalEvent]:
        """تحديث حدث مهني"""
        event = ProfessionalEvent.query.get(event_id)
        if not event:
            return None
        
        # تحديث البيانات
        for key, value in data.items():
            if hasattr(event, key):
                setattr(event, key, value)
        
        event.updated_at = datetime.utcnow()
        db.session.commit()
        
        # إعادة معالجة استحقاقات الموظف
        calculation_engine.process_employee_entitlements(event.employee)
        
        return event
    
    @staticmethod
    def delete_event(event_id: int) -> bool:
        """حذف حدث مهني"""
        event = ProfessionalEvent.query.get(event_id)
        if not event:
            return False
        
        employee = event.employee
        db.session.delete(event)
        db.session.commit()
        
        # إعادة معالجة استحقاقات الموظف
        calculation_engine.process_employee_entitlements(employee)
        
        return True
    
    @staticmethod
    def get_events_statistics() -> Dict[str, Any]:
        """الحصول على إحصائيات الأحداث المهنية"""
        # إحصائيات حسب النوع
        type_stats = db.session.query(
            ProfessionalEvent.event_type,
            func.count(ProfessionalEvent.id).label('count')
        ).group_by(ProfessionalEvent.event_type).all()
        
        # الأحداث الإيجابية والسلبية
        positive_events = ProfessionalEvent.query.filter(
            ProfessionalEvent.event_type.in_([EventType.COMMENDATION, EventType.HIGHER_DEGREE])
        ).count()
        
        negative_events = ProfessionalEvent.query.filter(
            ProfessionalEvent.event_type.in_([
                EventType.NOTICE_PENALTY, EventType.WARNING_PENALTY, EventType.REPRIMAND_PENALTY
            ])
        ).count()
        
        leave_events = ProfessionalEvent.query.filter(
            ProfessionalEvent.event_type.in_([
                EventType.UNPAID_LEAVE, EventType.DISABILITY_LEAVE,
                EventType.FIVE_YEAR_LEAVE, EventType.MATERNITY_LEAVE
            ])
        ).count()
        
        # الأحداث الحديثة (آخر 30 يوم)
        recent_events = ProfessionalEvent.query.filter(
            ProfessionalEvent.event_date >= date.today() - relativedelta(days=30)
        ).count()
        
        return {
            'type_stats': [{'type': event_type.value, 'count': count} for event_type, count in type_stats],
            'positive_events': positive_events,
            'negative_events': negative_events,
            'leave_events': leave_events,
            'recent_events': recent_events,
            'total_events': ProfessionalEvent.query.count()
        }

class PromotionHistoryService:
    """خدمة إدارة تاريخ الترفيعات"""
    
    @staticmethod
    def get_employee_promotion_history(employee_id: int) -> List[PromotionHistory]:
        """الحصول على تاريخ ترفيعات موظف"""
        return PromotionHistory.query.filter_by(employee_id=employee_id)\
                                   .order_by(desc(PromotionHistory.effective_date)).all()
    
    @staticmethod
    def get_all_promotions(page: int = 1, per_page: int = 20,
                          promotion_type: PromotionType = None,
                          date_from: date = None, date_to: date = None) -> Dict[str, Any]:
        """الحصول على جميع الترفيعات مع الفلترة"""
        query = PromotionHistory.query.options(joinedload(PromotionHistory.employee))
        
        # تطبيق الفلاتر
        if promotion_type:
            query = query.filter(PromotionHistory.promotion_type == promotion_type)
        
        if date_from:
            query = query.filter(PromotionHistory.effective_date >= date_from)
        
        if date_to:
            query = query.filter(PromotionHistory.effective_date <= date_to)
        
        # ترتيب حسب التاريخ
        query = query.order_by(desc(PromotionHistory.effective_date))
        
        # تطبيق الترقيم
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return {
            'promotions': pagination.items,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'prev_num': pagination.prev_num,
            'next_num': pagination.next_num
        }
    
    @staticmethod
    def get_promotion_statistics() -> Dict[str, Any]:
        """الحصول على إحصائيات الترفيعات"""
        # إحصائيات حسب النوع
        type_stats = db.session.query(
            PromotionHistory.promotion_type,
            func.count(PromotionHistory.id).label('count')
        ).group_by(PromotionHistory.promotion_type).all()
        
        # الترفيعات الحديثة (آخر 30 يوم)
        recent_promotions = PromotionHistory.query.filter(
            PromotionHistory.effective_date >= date.today() - relativedelta(days=30)
        ).count()
        
        # إحصائيات شهرية (آخر 12 شهر)
        monthly_stats = []
        for i in range(12):
            month_start = date.today().replace(day=1) - relativedelta(months=i)
            month_end = month_start + relativedelta(months=1) - relativedelta(days=1)
            
            count = PromotionHistory.query.filter(
                and_(
                    PromotionHistory.effective_date >= month_start,
                    PromotionHistory.effective_date <= month_end
                )
            ).count()
            
            monthly_stats.append({
                'month': month_start.strftime('%Y-%m'),
                'count': count
            })
        
        return {
            'type_stats': [{'type': ptype.value, 'count': count} for ptype, count in type_stats],
            'recent_promotions': recent_promotions,
            'monthly_stats': list(reversed(monthly_stats)),
            'total_promotions': PromotionHistory.query.count()
        }

# إنشاء مثيلات الخدمات
employee_service = EmployeeService()
professional_event_service = ProfessionalEventService()
promotion_history_service = PromotionHistoryService()

