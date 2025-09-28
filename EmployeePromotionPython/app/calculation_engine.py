from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from typing import List, Tuple, Optional
from .models import Employee, ProfessionalEvent, PromotionHistory, EventType, PromotionType, db

class CalculationEngine:
    """المحرك الذكي لحساب العلاوات والترفيعات"""
    
    def __init__(self):
        self.base_allowance_period_months = 12  # المدة الأساسية للعلاوة (12 شهر)
    
    def process_employee_entitlements(self, employee: Employee) -> List[PromotionHistory]:
        """
        معالجة استحقاقات الموظف وحساب العلاوات والترفيعات التلقائية
        
        Args:
            employee: الموظف المراد معالجة استحقاقاته
            
        Returns:
            قائمة بالعلاوات والترفيعات الجديدة
        """
        new_records = []
        
        # نقطة البداية للحساب
        current_date = employee.last_allowance_date
        today = date.today()
        
        # الحالة الحالية للموظف
        current_grade = employee.job_grade
        current_stage = employee.job_stage
        current_tracker = employee.allowance_tracker
        
        # حلقة المعالجة
        while True:
            # حساب تاريخ الاستحقاق التالي
            next_entitlement_date = self._calculate_next_entitlement_date(
                employee, current_date
            )
            
            # إذا كان التاريخ في المستقبل، توقف
            if next_entitlement_date > today:
                break
            
            # تحديد نوع الاستحقاق
            entitlement_type = self._determine_entitlement_type(
                current_grade, current_tracker
            )
            
            if entitlement_type == "لا يوجد استحقاق":
                break
            
            # تنفيذ الاستحقاق
            if entitlement_type == "علاوة":
                record = self._process_allowance(
                    employee, next_entitlement_date, current_grade, current_stage
                )
                current_stage += 1
                current_tracker = self._update_tracker(current_tracker, False)
                
            else:  # ترفيع
                record = self._process_promotion(
                    employee, next_entitlement_date, current_grade, current_stage
                )
                current_grade -= 1
                current_stage = 1
                current_tracker = self._reset_tracker(current_grade)
            
            new_records.append(record)
            current_date = next_entitlement_date
        
        # تحديث بيانات الموظف
        employee.job_grade = current_grade
        employee.job_stage = current_stage
        employee.allowance_tracker = current_tracker
        employee.last_allowance_date = current_date
        
        # حفظ السجلات الجديدة
        for record in new_records:
            db.session.add(record)
        
        db.session.commit()
        
        return new_records
    
    def _calculate_next_entitlement_date(self, employee: Employee, base_date: date) -> date:
        """
        حساب تاريخ الاستحقاق التالي مع مراعاة تأثيرات الأحداث المهنية
        
        Args:
            employee: الموظف
            base_date: التاريخ الأساسي للحساب
            
        Returns:
            تاريخ الاستحقاق التالي
        """
        # البداية: إضافة 12 شهراً
        next_date = base_date + relativedelta(months=self.base_allowance_period_months)
        
        # تطبيق تأثيرات الأحداث المهنية
        relevant_events = employee.professional_events.filter(
            ProfessionalEvent.event_date >= base_date
        ).all()
        
        for event in relevant_events:
            if event.impact_months != 0:
                # تطبيق التأثير
                next_date += relativedelta(months=event.impact_months)
        
        return next_date
    
    def _determine_entitlement_type(self, grade: int, tracker: str) -> str:
        """
        تحديد نوع الاستحقاق القادم
        
        Args:
            grade: الدرجة الحالية
            tracker: مؤشر التتبع الحالي
            
        Returns:
            نوع الاستحقاق ("علاوة"، "ترفيع"، "لا يوجد استحقاق")
        """
        # الدرجة الأولى - علاوات فقط
        if grade == 1:
            # استخراج المرحلة من المؤشر أو حساب آخر
            # إذا وصل للمرحلة 11، لا يوجد استحقاق
            return "لا يوجد استحقاق" if "11" in tracker else "علاوة"
        
        # الدرجات الأخرى
        if '/' in tracker:
            current, total = map(int, tracker.split('/'))
            # إذا وصل للحد الأقصى، الاستحقاق القادم ترفيع
            return "ترفيع" if current >= total - 1 else "علاوة"
        
        return "علاوة"
    
    def _process_allowance(self, employee: Employee, effective_date: date, 
                          current_grade: int, current_stage: int) -> PromotionHistory:
        """
        معالجة علاوة سنوية
        
        Args:
            employee: الموظف
            effective_date: تاريخ السريان
            current_grade: الدرجة الحالية
            current_stage: المرحلة الحالية
            
        Returns:
            سجل العلاوة الجديد
        """
        new_stage = current_stage + 1
        
        record = PromotionHistory(
            employee_id=employee.id,
            promotion_type=PromotionType.ALLOWANCE,
            effective_date=effective_date,
            from_grade=current_grade,
            to_grade=current_grade,
            from_stage=current_stage,
            to_stage=new_stage,
            description=f"علاوة سنوية - انتقال من المرحلة {current_stage} إلى المرحلة {new_stage}",
            impact="زيادة في الراتب الأساسي"
        )
        
        return record
    
    def _process_promotion(self, employee: Employee, effective_date: date,
                          current_grade: int, current_stage: int) -> PromotionHistory:
        """
        معالجة ترفيع وظيفي
        
        Args:
            employee: الموظف
            effective_date: تاريخ السريان
            current_grade: الدرجة الحالية
            current_stage: المرحلة الحالية
            
        Returns:
            سجل الترفيع الجديد
        """
        new_grade = current_grade - 1
        new_stage = 1
        
        record = PromotionHistory(
            employee_id=employee.id,
            promotion_type=PromotionType.PROMOTION,
            effective_date=effective_date,
            from_grade=current_grade,
            to_grade=new_grade,
            from_stage=current_stage,
            to_stage=new_stage,
            description=f"ترفيع وظيفي - من الدرجة {current_grade} إلى الدرجة {new_grade}",
            impact="ترفيع في الدرجة الوظيفية وزيادة في الراتب"
        )
        
        return record
    
    def _update_tracker(self, current_tracker: str, is_promotion: bool) -> str:
        """
        تحديث مؤشر التتبع
        
        Args:
            current_tracker: المؤشر الحالي
            is_promotion: هل هو ترفيع أم علاوة
            
        Returns:
            المؤشر المحدث
        """
        if '/' in current_tracker:
            current, total = map(int, current_tracker.split('/'))
            if is_promotion:
                return f"0/{total}"  # إعادة تصفير بعد الترفيع
            else:
                return f"{current + 1}/{total}"  # زيادة العداد
        
        return current_tracker
    
    def _reset_tracker(self, new_grade: int) -> str:
        """
        إعادة تعيين مؤشر التتبع بعد الترفيع
        
        Args:
            new_grade: الدرجة الجديدة
            
        Returns:
            المؤشر الجديد
        """
        # تحديد نوع المؤشر حسب الدرجة
        if new_grade >= 6:  # الدرجات 10-6
            return "0/4"
        elif new_grade >= 2:  # الدرجات 5-2
            return "0/5"
        else:  # الدرجة الأولى
            return "0/10"  # علاوات فقط حتى المرحلة 11
    
    def validate_professional_event(self, employee: Employee, event_type: EventType, 
                                  event_date: date, **kwargs) -> Tuple[bool, str]:
        """
        التحقق من صحة الحدث المهني وتطبيق القواعد والقيود
        
        Args:
            employee: الموظف
            event_type: نوع الحدث
            event_date: تاريخ الحدث
            **kwargs: معاملات إضافية
            
        Returns:
            (صحيح/خطأ، رسالة الخطأ إن وجدت)
        """
        if event_type == EventType.COMMENDATION:
            return self._validate_commendation(employee, event_date, kwargs.get('reduction_months', 0))
        
        elif event_type == EventType.HIGHER_DEGREE:
            return self._validate_higher_degree(employee, event_date)
        
        elif event_type in [EventType.NOTICE_PENALTY, EventType.WARNING_PENALTY, EventType.REPRIMAND_PENALTY]:
            return self._validate_penalty(employee, event_type, event_date)
        
        elif event_type in [EventType.UNPAID_LEAVE, EventType.DISABILITY_LEAVE, 
                           EventType.FIVE_YEAR_LEAVE, EventType.MATERNITY_LEAVE]:
            return self._validate_leave(employee, event_type, event_date, 
                                      kwargs.get('start_date'), kwargs.get('end_date'))
        
        return True, ""
    
    def _validate_commendation(self, employee: Employee, event_date: date, reduction_months: int) -> Tuple[bool, str]:
        """التحقق من صحة كتاب الشكر"""
        year = event_date.year
        
        # عدد كتب الشكر في نفس السنة
        commendations_this_year = employee.professional_events.filter(
            ProfessionalEvent.event_type == EventType.COMMENDATION,
            db.extract('year', ProfessionalEvent.event_date) == year
        ).count()
        
        # عدد كتب الشكر بمدة 6 أشهر في المسيرة الوظيفية
        six_month_commendations = employee.professional_events.filter(
            ProfessionalEvent.event_type == EventType.COMMENDATION,
            ProfessionalEvent.impact_months == -6
        ).count()
        
        # تطبيق القواعد
        if reduction_months == 6:
            if six_month_commendations >= 2:
                return False, "لا يسمح بأكثر من كتابي شكر بمدة 6 أشهر طوال المسيرة الوظيفية"
            if commendations_this_year >= 1:
                return False, "يمكن إضافة كتاب شكر واحد فقط بمدة 6 أشهر في السنة"
        else:
            if commendations_this_year >= 3:
                return False, "لا يسمح بأكثر من 3 كتب شكر (أقل من 6 أشهر) في السنة الواحدة"
        
        return True, ""
    
    def _validate_higher_degree(self, employee: Employee, event_date: date) -> Tuple[bool, str]:
        """التحقق من صحة الشهادة الأعلى"""
        # يمكن إضافة قواعد خاصة بالشهادات هنا
        return True, ""
    
    def _validate_penalty(self, employee: Employee, event_type: EventType, event_date: date) -> Tuple[bool, str]:
        """التحقق من صحة العقوبة"""
        # يمكن إضافة قواعد خاصة بالعقوبات هنا
        return True, ""
    
    def _validate_leave(self, employee: Employee, event_type: EventType, event_date: date,
                       start_date: Optional[date], end_date: Optional[date]) -> Tuple[bool, str]:
        """التحقق من صحة الإجازة"""
        if not start_date or not end_date:
            return False, "يجب تحديد تاريخي بداية ونهاية الإجازة"
        
        if end_date <= start_date:
            return False, "تاريخ نهاية الإجازة يجب أن يكون بعد تاريخ البداية"
        
        # التحقق من عدم تداخل الإجازات
        overlapping_leaves = employee.professional_events.filter(
            ProfessionalEvent.event_type.in_([
                EventType.UNPAID_LEAVE, EventType.DISABILITY_LEAVE,
                EventType.FIVE_YEAR_LEAVE, EventType.MATERNITY_LEAVE
            ]),
            ProfessionalEvent.start_date <= end_date,
            ProfessionalEvent.end_date >= start_date
        ).count()
        
        if overlapping_leaves > 0:
            return False, "يوجد تداخل مع إجازة أخرى في نفس الفترة"
        
        return True, ""
    
    def calculate_event_impact(self, event_type: EventType, **kwargs) -> int:
        """
        حساب تأثير الحدث المهني بالأشهر
        
        Args:
            event_type: نوع الحدث
            **kwargs: معاملات إضافية
            
        Returns:
            التأثير بالأشهر (+ للإضافة، - للتقليص)
        """
        if event_type == EventType.COMMENDATION:
            return -kwargs.get('reduction_months', 0)
        
        elif event_type == EventType.HIGHER_DEGREE:
            return -12  # Step (12 شهر)
        
        elif event_type == EventType.NOTICE_PENALTY:
            return 3
        
        elif event_type == EventType.WARNING_PENALTY:
            return 6
        
        elif event_type == EventType.REPRIMAND_PENALTY:
            return 12
        
        elif event_type in [EventType.UNPAID_LEAVE, EventType.DISABILITY_LEAVE,
                           EventType.FIVE_YEAR_LEAVE, EventType.MATERNITY_LEAVE]:
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            if start_date and end_date:
                days = (end_date - start_date).days
                return int(days / 30)  # تحويل الأيام إلى أشهر تقريبياً
        
        elif event_type == EventType.CUSTOM:
            adjustment_type = kwargs.get('adjustment_type', 'add')
            months = kwargs.get('months', 0)
            return months if adjustment_type == 'add' else -months
        
        return 0

# إنشاء مثيل عام من المحرك
calculation_engine = CalculationEngine()

