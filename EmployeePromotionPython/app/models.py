from datetime import datetime, date
from enum import Enum
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, Date, Text, Float, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from dateutil.relativedelta import relativedelta

db = SQLAlchemy()

class EventType(Enum):
    """أنواع الأحداث المهنية"""
    NONE = "none"
    COMMENDATION = "commendation"  # كتاب شكر وتقدير
    HIGHER_DEGREE = "higher_degree"  # شهادة أعلى
    NOTICE_PENALTY = "notice_penalty"  # عقوبة لفت نظر
    WARNING_PENALTY = "warning_penalty"  # عقوبة إنذار
    REPRIMAND_PENALTY = "reprimand_penalty"  # عقوبة توبيخ
    UNPAID_LEAVE = "unpaid_leave"  # إجازة بدون راتب
    DISABILITY_LEAVE = "disability_leave"  # إجازة رعاية المعاقين
    FIVE_YEAR_LEAVE = "five_year_leave"  # إجازة الخمس سنوات
    MATERNITY_LEAVE = "maternity_leave"  # إجازة أمومة
    CUSTOM = "custom"  # حدث مخصص

class PromotionType(Enum):
    """أنواع الترفيعات"""
    ALLOWANCE = "allowance"  # علاوة
    PROMOTION = "promotion"  # ترفيع

class Employee(db.Model):
    """نموذج الموظف"""
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True)
    full_name = Column(String(200), nullable=False, index=True)
    title = Column(String(100))  # اللقب العلمي
    job_category = Column(String(50), nullable=False, index=True)  # صنف الوظيفة
    academic_degree = Column(String(50))  # الشهادة العلمية
    job_grade = Column(Integer, nullable=False, index=True)  # الدرجة الوظيفية
    job_stage = Column(Integer, nullable=False)  # المرحلة الوظيفية
    job_title_number = Column(Integer)  # العنوان الوظيفي (رقم)
    allowance_tracker = Column(String(10), nullable=False)  # مؤشر تتبع العلاوة
    start_date = Column(Date, nullable=False, index=True)  # تاريخ المباشرة
    last_allowance_date = Column(Date, nullable=False)  # تاريخ آخر استحقاق للعلاوة
    last_promotion_date = Column(Date, nullable=False)  # آخر تاريخ استحقاق للترفيع
    photo_path = Column(String(255))  # مسار صورة الموظف
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    professional_events = relationship('ProfessionalEvent', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    promotion_history = relationship('PromotionHistory', backref='employee', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Employee {self.full_name}>'
    
    @property
    def actual_service_years(self):
        """حساب سنوات الخدمة الفعلية"""
        today = date.today()
        service_period = relativedelta(today, self.start_date)
        
        # طرح فترات الإجازات الطويلة
        leave_days = 0
        for event in self.professional_events:
            if event.event_type in [EventType.UNPAID_LEAVE, EventType.DISABILITY_LEAVE, 
                                  EventType.FIVE_YEAR_LEAVE, EventType.MATERNITY_LEAVE]:
                if event.start_date and event.end_date:
                    leave_period = (event.end_date - event.start_date).days
                    leave_days += leave_period
        
        # تحويل أيام الإجازة إلى سنوات وطرحها
        leave_years = leave_days / 365.25
        total_years = service_period.years + (service_period.months / 12.0) + (service_period.days / 365.25)
        actual_years = max(0, total_years - leave_years)
        
        return actual_years
    
    @property
    def actual_service_formatted(self):
        """تنسيق سنوات الخدمة الفعلية"""
        total_years = self.actual_service_years
        years = int(total_years)
        months = int((total_years - years) * 12)
        days = int(((total_years - years) * 12 - months) * 30)
        
        return f"{years} سنة، {months} شهر، {days} يوم"
    
    @property
    def next_entitlement_type(self):
        """تحديد نوع الاستحقاق القادم"""
        if self.job_grade == 1:
            # الدرجة الأولى - علاوات فقط
            if self.job_stage >= 11:
                return "لا يوجد استحقاق"
            return "علاوة"
        
        # تحليل مؤشر التتبع
        if '/' in self.allowance_tracker:
            current, total = map(int, self.allowance_tracker.split('/'))
            if current >= total - 1:
                return "ترفيع"
            return "علاوة"
        
        return "علاوة"
    
    @property
    def next_entitlement_date(self):
        """حساب تاريخ الاستحقاق القادم"""
        base_date = self.last_allowance_date
        
        # إضافة 12 شهراً كأساس
        next_date = base_date + relativedelta(months=12)
        
        # تطبيق تأثيرات الأحداث المهنية
        for event in self.professional_events:
            if event.event_date >= base_date:
                if event.impact_months != 0:
                    if event.impact_months > 0:
                        # إضافة مدة (عقوبة أو إجازة)
                        next_date += relativedelta(months=event.impact_months)
                    else:
                        # تقليص مدة (كتاب شكر أو شهادة)
                        next_date += relativedelta(months=event.impact_months)
        
        return next_date
    
    def to_dict(self):
        """تحويل الموظف إلى قاموس"""
        return {
            'id': self.id,
            'full_name': self.full_name,
            'title': self.title,
            'job_category': self.job_category,
            'academic_degree': self.academic_degree,
            'job_grade': self.job_grade,
            'job_stage': self.job_stage,
            'job_title_number': self.job_title_number,
            'allowance_tracker': self.allowance_tracker,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'last_allowance_date': self.last_allowance_date.isoformat() if self.last_allowance_date else None,
            'last_promotion_date': self.last_promotion_date.isoformat() if self.last_promotion_date else None,
            'photo_path': self.photo_path,
            'actual_service_formatted': self.actual_service_formatted,
            'next_entitlement_type': self.next_entitlement_type,
            'next_entitlement_date': self.next_entitlement_date.isoformat() if self.next_entitlement_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ProfessionalEvent(db.Model):
    """نموذج الأحداث المهنية"""
    __tablename__ = 'professional_events'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False, index=True)
    event_type = Column(SQLEnum(EventType), nullable=False, index=True)
    event_date = Column(Date, nullable=False, index=True)
    description = Column(Text)
    document_number = Column(String(100))  # رقم الكتاب الرسمي
    document_date = Column(Date)  # تاريخ الكتاب الرسمي
    impact_months = Column(Integer, default=0)  # التأثير بالأشهر (+ أو -)
    start_date = Column(Date)  # تاريخ البداية (للإجازات)
    end_date = Column(Date)  # تاريخ النهاية (للإجازات)
    notes = Column(Text)  # ملاحظات إضافية
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProfessionalEvent {self.event_type.value} for {self.employee.full_name}>'
    
    @property
    def event_type_name(self):
        """اسم نوع الحدث بالعربية"""
        names = {
            EventType.COMMENDATION: "كتاب شكر وتقدير",
            EventType.HIGHER_DEGREE: "الحصول على شهادة أعلى",
            EventType.NOTICE_PENALTY: "عقوبة لفت نظر",
            EventType.WARNING_PENALTY: "عقوبة إنذار",
            EventType.REPRIMAND_PENALTY: "عقوبة توبيخ",
            EventType.UNPAID_LEAVE: "إجازة بدون راتب",
            EventType.DISABILITY_LEAVE: "إجازة رعاية المعاقين",
            EventType.FIVE_YEAR_LEAVE: "إجازة الخمس سنوات",
            EventType.MATERNITY_LEAVE: "إجازة أمومة",
            EventType.CUSTOM: "حدث مخصص"
        }
        return names.get(self.event_type, "حدث غير محدد")
    
    @property
    def event_category(self):
        """تصنيف الحدث (إيجابي، سلبي، محايد)"""
        if self.event_type in [EventType.COMMENDATION, EventType.HIGHER_DEGREE]:
            return "positive"
        elif self.event_type in [EventType.NOTICE_PENALTY, EventType.WARNING_PENALTY, EventType.REPRIMAND_PENALTY]:
            return "negative"
        else:
            return "neutral"
    
    def to_dict(self):
        """تحويل الحدث إلى قاموس"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'event_type': self.event_type.value,
            'event_type_name': self.event_type_name,
            'event_category': self.event_category,
            'event_date': self.event_date.isoformat() if self.event_date else None,
            'description': self.description,
            'document_number': self.document_number,
            'document_date': self.document_date.isoformat() if self.document_date else None,
            'impact_months': self.impact_months,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class PromotionHistory(db.Model):
    """نموذج تاريخ الترفيعات والعلاوات"""
    __tablename__ = 'promotion_history'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False, index=True)
    promotion_type = Column(SQLEnum(PromotionType), nullable=False)
    effective_date = Column(Date, nullable=False, index=True)
    from_grade = Column(Integer)  # من الدرجة
    to_grade = Column(Integer)  # إلى الدرجة
    from_stage = Column(Integer)  # من المرحلة
    to_stage = Column(Integer)  # إلى المرحلة
    description = Column(Text)
    impact = Column(String(200))  # التأثير
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PromotionHistory {self.promotion_type.value} for {self.employee.full_name}>'
    
    @property
    def type_name(self):
        """اسم نوع الترفيع بالعربية"""
        return "ترفيع" if self.promotion_type == PromotionType.PROMOTION else "علاوة سنوية"
    
    def to_dict(self):
        """تحويل السجل إلى قاموس"""
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'promotion_type': self.promotion_type.value,
            'type_name': self.type_name,
            'effective_date': self.effective_date.isoformat() if self.effective_date else None,
            'from_grade': self.from_grade,
            'to_grade': self.to_grade,
            'from_stage': self.from_stage,
            'to_stage': self.to_stage,
            'description': self.description,
            'impact': self.impact,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

