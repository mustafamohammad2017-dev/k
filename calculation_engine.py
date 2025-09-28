#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
المحرك الذكي لحساب العلاوات والترفيعات
Intelligent Calculation Engine for Allowances and Promotions
"""

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import sqlite3
from typing import List, Dict, Tuple, Optional

class CalculationEngine:
    """المحرك الذكي لحساب العلاوات والترفيعات"""
    
    def __init__(self, db_connection):
        self.conn = db_connection
        self.cursor = db_connection.cursor()
    
    def calculate_employee_status(self, employee_id: int) -> Dict:
        """
        حساب الحالة الحالية للموظف وتحديث سجله
        """
        # جلب بيانات الموظف
        employee = self.get_employee_data(employee_id)
        if not employee:
            return {"error": "الموظف غير موجود"}
        
        # جلب الأحداث المهنية
        events = self.get_professional_events(employee_id)
        
        # تطبيق المحرك الذكي
        result = self.apply_calculation_engine(employee, events)
        
        # تحديث قاعدة البيانات
        self.update_employee_status(employee_id, result)
        
        return result
    
    def get_employee_data(self, employee_id: int) -> Optional[Dict]:
        """جلب بيانات الموظف"""
        self.cursor.execute("""
            SELECT id, full_name, start_date, last_allowance_date, last_promotion_date,
                   promotion_tracker, academic_degree, job_category, job_title, job_grade
            FROM employees WHERE id = ?
        """, (employee_id,))
        
        row = self.cursor.fetchone()
        if not row:
            return None
        
        return {
            'id': row[0],
            'full_name': row[1],
            'start_date': datetime.strptime(row[2], "%Y-%m-%d"),
            'last_allowance_date': datetime.strptime(row[3], "%Y-%m-%d"),
            'last_promotion_date': datetime.strptime(row[4], "%Y-%m-%d"),
            'promotion_tracker': row[5],
            'academic_degree': row[6],
            'job_category': row[7],
            'job_title': row[8],
            'job_grade': row[9]
        }
    
    def get_professional_events(self, employee_id: int) -> List[Dict]:
        """جلب الأحداث المهنية للموظف"""
        self.cursor.execute("""
            SELECT event_type, event_date, impact_months, start_date, end_date, description
            FROM professional_events
            WHERE employee_id = ?
            ORDER BY event_date
        """, (employee_id,))
        
        events = []
        for row in self.cursor.fetchall():
            event = {
                'event_type': row[0],
                'event_date': datetime.strptime(row[1], "%Y-%m-%d"),
                'impact_months': row[2] or 0,
                'start_date': datetime.strptime(row[3], "%Y-%m-%d") if row[3] else None,
                'end_date': datetime.strptime(row[4], "%Y-%m-%d") if row[4] else None,
                'description': row[5]
            }
            events.append(event)
        
        return events
    
    def apply_calculation_engine(self, employee: Dict, events: List[Dict]) -> Dict:
        """تطبيق المحرك الذكي للحسابات"""
        
        # نقطة البداية
        current_date = datetime.now()
        last_allowance_date = employee['last_allowance_date']
        promotion_tracker = employee['promotion_tracker']
        job_grade = employee['job_grade']
        
        # تحليل مؤشر التتبع
        tracker_parts = promotion_tracker.split('/')
        current_stage = int(tracker_parts[0])
        max_stages = int(tracker_parts[1])
        
        # قائمة العلاوات والترفيعات المحسوبة
        calculated_events = []
        
        # نقطة الارتكاز الزمنية
        anchor_date = last_allowance_date
        
        # حلقة الحساب الذكي
        while anchor_date < current_date:
            # حساب تاريخ الاستحقاق التالي (12 شهر)
            next_due_date = anchor_date + relativedelta(months=12)
            
            # تطبيق تأثير الأحداث المهنية
            next_due_date = self.apply_events_impact(next_due_date, events, anchor_date)
            
            # التحقق من وصول تاريخ الاستحقاق
            if next_due_date <= current_date:
                # تحديد نوع الحدث (علاوة أم ترفيع)
                event_type, new_grade, new_stage, new_tracker = self.determine_event_type(
                    job_grade, current_stage, max_stages
                )
                
                # تسجيل الحدث
                calculated_events.append({
                    'event_type': event_type,
                    'event_date': next_due_date,
                    'from_grade': job_grade,
                    'to_grade': new_grade,
                    'from_stage': current_stage,
                    'to_stage': new_stage,
                    'description': self.generate_event_description(event_type, job_grade, new_grade, current_stage, new_stage)
                })
                
                # تحديث المتغيرات
                job_grade = new_grade
                current_stage = new_stage
                promotion_tracker = new_tracker
                anchor_date = next_due_date
            else:
                break
        
        # حساب الاستحقاق القادم
        next_due_date = anchor_date + relativedelta(months=12)
        next_due_date = self.apply_events_impact(next_due_date, events, anchor_date)
        
        next_event_type, next_grade, next_stage, _ = self.determine_event_type(
            job_grade, current_stage, max_stages
        )
        
        # حساب الخدمة الفعلية
        effective_service = self.calculate_effective_service(employee['start_date'], events)
        
        return {
            'current_grade': job_grade,
            'current_stage': current_stage,
            'promotion_tracker': promotion_tracker,
            'calculated_events': calculated_events,
            'next_due_date': next_due_date,
            'next_event_type': next_event_type,
            'next_grade': next_grade,
            'next_stage': next_stage,
            'effective_service': effective_service
        }
    
    def determine_event_type(self, current_grade: int, current_stage: int, max_stages: int) -> Tuple[str, int, int, str]:
        """تحديد نوع الحدث القادم (علاوة أم ترفيع)"""
        
        # للدرجات من 10 إلى 6 (نظام 4 مراحل)
        if current_grade >= 6 and max_stages == 4:
            if current_stage < 3:
                # علاوة
                new_stage = current_stage + 1
                new_tracker = f"{new_stage}/4"
                return "علاوة", current_grade, new_stage, new_tracker
            else:
                # ترفيع
                new_grade = current_grade - 1
                new_stage = 0
                new_tracker = "0/4" if new_grade >= 6 else "0/5"
                return "ترفيع", new_grade, new_stage, new_tracker
        
        # للدرجات من 5 إلى 2 (نظام 5 مراحل)
        elif current_grade >= 2 and max_stages == 5:
            if current_stage < 4:
                # علاوة
                new_stage = current_stage + 1
                new_tracker = f"{new_stage}/5"
                return "علاوة", current_grade, new_stage, new_tracker
            else:
                # ترفيع
                new_grade = current_grade - 1
                new_stage = 0
                new_tracker = "0/5" if new_grade >= 2 else "0/10"
                return "ترفيع", new_grade, new_stage, new_tracker
        
        # للدرجة الأولى (نظام 10 مراحل)
        elif current_grade == 1:
            if current_stage < 10:
                # علاوة
                new_stage = current_stage + 1
                new_tracker = f"{new_stage}/10"
                return "علاوة", current_grade, new_stage, new_tracker
            else:
                # لا يوجد ترفيع من الدرجة الأولى
                return "انتهاء", current_grade, current_stage, f"{current_stage}/10"
        
        return "علاوة", current_grade, current_stage + 1, f"{current_stage + 1}/{max_stages}"
    
    def apply_events_impact(self, due_date: datetime, events: List[Dict], anchor_date: datetime) -> datetime:
        """تطبيق تأثير الأحداث المهنية على تاريخ الاستحقاق"""
        
        for event in events:
            event_date = event['event_date']
            
            # تطبيق الأحداث التي حدثت بعد نقطة الارتكاز وقبل تاريخ الاستحقاق
            if anchor_date <= event_date <= due_date:
                
                if event['event_type'] in ['كتاب_شكر', 'شهادة_عليا']:
                    # تقليص المدة
                    due_date = due_date - relativedelta(months=event['impact_months'])
                
                elif event['event_type'] in ['عقوبة_لفت_نظر', 'عقوبة_انذار', 'عقوبة_توبيخ']:
                    # زيادة المدة
                    due_date = due_date + relativedelta(months=event['impact_months'])
                
                elif event['event_type'] in ['اجازة_بدون_راتب', 'اجازة_رعاية_معاقين', 'اجازة_خمس_سنوات']:
                    # تجميد الخدمة
                    if event['start_date'] and event['end_date']:
                        freeze_duration = (event['end_date'] - event['start_date']).days
                        due_date = due_date + timedelta(days=freeze_duration)
        
        return due_date
    
    def calculate_effective_service(self, start_date: datetime, events: List[Dict]) -> Dict:
        """حساب الخدمة الفعلية"""
        
        current_date = datetime.now()
        total_days = (current_date - start_date).days
        
        # طرح فترات الإجازات الطويلة
        freeze_days = 0
        for event in events:
            if event['event_type'] in ['اجازة_بدون_راتب', 'اجازة_رعاية_معاقين', 'اجازة_خمس_سنوات']:
                if event['start_date'] and event['end_date']:
                    freeze_days += (event['end_date'] - event['start_date']).days
        
        effective_days = total_days - freeze_days
        effective_years = effective_days // 365
        effective_months = (effective_days % 365) // 30
        remaining_days = (effective_days % 365) % 30
        
        return {
            'total_days': effective_days,
            'years': effective_years,
            'months': effective_months,
            'days': remaining_days,
            'text': f"{effective_years} سنة، {effective_months} شهر، {remaining_days} يوم"
        }
    
    def generate_event_description(self, event_type: str, from_grade: int, to_grade: int, from_stage: int, to_stage: int) -> str:
        """توليد وصف للحدث"""
        if event_type == "علاوة":
            return f"علاوة سنوية - انتقال من المرحلة {from_stage} إلى المرحلة {to_stage} في الدرجة {from_grade}"
        elif event_type == "ترفيع":
            return f"ترفيع وظيفي - انتقال من الدرجة {from_grade} المرحلة {from_stage} إلى الدرجة {to_grade} المرحلة {to_stage}"
        else:
            return f"حدث وظيفي: {event_type}"
    
    def update_employee_status(self, employee_id: int, result: Dict):
        """تحديث حالة الموظف في قاعدة البيانات"""
        
        # تحديث بيانات الموظف الأساسية
        self.cursor.execute("""
            UPDATE employees 
            SET job_grade = ?, promotion_tracker = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (result['current_grade'], result['promotion_tracker'], employee_id))
        
        # حذف السجلات المحسوبة السابقة
        self.cursor.execute("""
            DELETE FROM career_history 
            WHERE employee_id = ? AND description LIKE '%محسوب تلقائياً%'
        """, (employee_id,))
        
        # إدراج الأحداث المحسوبة الجديدة
        for event in result['calculated_events']:
            self.cursor.execute("""
                INSERT INTO career_history (
                    employee_id, event_type, event_date, from_grade, to_grade,
                    from_stage, to_stage, description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                employee_id,
                event['event_type'],
                event['event_date'].strftime("%Y-%m-%d"),
                event['from_grade'],
                event['to_grade'],
                event['from_stage'],
                event['to_stage'],
                event['description'] + " (محسوب تلقائياً)"
            ))
        
        self.conn.commit()
    
    def handle_special_cases(self, employee: Dict) -> bool:
        """التعامل مع الحالات الخاصة"""
        
        # قاعدة الترفيع السريع للموظفين الجدد
        if (employee['start_date'] == employee['last_allowance_date'] and 
            employee['job_grade'] == 8 and 
            'دبلوم' in employee['academic_degree'].lower()):
            
            # الاستحقاق الأول هو ترفيع مباشر إلى الدرجة 7
            return True
        
        return False
    
    def get_next_allowance_info(self, employee_id: int) -> Dict:
        """الحصول على معلومات الاستحقاق القادم"""
        result = self.calculate_employee_status(employee_id)
        
        return {
            'next_due_date': result['next_due_date'],
            'event_type': result['next_event_type'],
            'current_grade': result['current_grade'],
            'current_stage': result['current_stage'],
            'next_grade': result['next_grade'],
            'next_stage': result['next_stage']
        }
