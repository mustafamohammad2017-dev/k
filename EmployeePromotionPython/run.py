#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام أتمتة العلاوات والترفيعات الوظيفية
Employee Promotion Automation System

ملف التشغيل الرئيسي للتطبيق
"""

import os
import sys
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# إضافة مسار التطبيق إلى Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Employee, ProfessionalEvent, PromotionHistory, EventType, PromotionType
from app.services import employee_service, professional_event_service
from app.calculation_engine import calculation_engine

def create_sample_data():
    """إنشاء بيانات تجريبية للنظام"""
    
    print("🔄 إنشاء البيانات التجريبية...")
    
    # التحقق من وجود بيانات مسبقاً
    if Employee.query.count() > 0:
        print("✅ البيانات موجودة مسبقاً")
        return
    
    try:
        # إنشاء موظفين تجريبيين
        employees_data = [
            {
                'full_name': 'د. أحمد محمد علي',
                'title': 'دكتور',
                'job_category': 'تدريسي',
                'academic_degree': 'دكتوراه',
                'job_grade': 7,
                'job_stage': 2,
                'job_title_number': 101,
                'allowance_tracker': '1/4',
                'start_date': date(2020, 9, 1),
                'last_allowance_date': date(2023, 9, 1),
                'last_promotion_date': date(2020, 9, 1)
            },
            {
                'full_name': 'أ.م.د. فاطمة حسن محمود',
                'title': 'أستاذ مساعد دكتور',
                'job_category': 'تدريسي',
                'academic_degree': 'دكتوراه',
                'job_grade': 6,
                'job_stage': 3,
                'job_title_number': 102,
                'allowance_tracker': '2/4',
                'start_date': date(2018, 2, 15),
                'last_allowance_date': date(2023, 2, 15),
                'last_promotion_date': date(2021, 2, 15)
            },
            {
                'full_name': 'م. خالد عبد الرحمن',
                'title': 'مهندس',
                'job_category': 'إداري',
                'academic_degree': 'بكالوريوس',
                'job_grade': 8,
                'job_stage': 1,
                'job_title_number': 201,
                'allowance_tracker': '0/4',
                'start_date': date(2021, 6, 1),
                'last_allowance_date': date(2021, 6, 1),
                'last_promotion_date': date(2021, 6, 1)
            },
            {
                'full_name': 'أ. مريم سالم أحمد',
                'title': 'أستاذ',
                'job_category': 'تدريسي',
                'academic_degree': 'ماجستير',
                'job_grade': 9,
                'job_stage': 4,
                'job_title_number': 103,
                'allowance_tracker': '3/4',
                'start_date': date(2019, 10, 1),
                'last_allowance_date': date(2023, 10, 1),
                'last_promotion_date': date(2019, 10, 1)
            },
            {
                'full_name': 'السيد علي حسين جعفر',
                'title': '',
                'job_category': 'فني',
                'academic_degree': 'دبلوم',
                'job_grade': 10,
                'job_stage': 2,
                'job_title_number': 301,
                'allowance_tracker': '1/4',
                'start_date': date(2022, 1, 15),
                'last_allowance_date': date(2023, 1, 15),
                'last_promotion_date': date(2022, 1, 15)
            }
        ]
        
        created_employees = []
        for emp_data in employees_data:
            employee = employee_service.create_employee(emp_data)
            created_employees.append(employee)
            print(f"✅ تم إنشاء الموظف: {employee.full_name}")
        
        # إنشاء أحداث مهنية تجريبية
        events_data = [
            {
                'employee_id': created_employees[0].id,
                'event_type': EventType.COMMENDATION.value,
                'event_date': date(2023, 5, 15),
                'description': 'كتاب شكر وتقدير للأداء المتميز',
                'document_number': 'ش/123/2023',
                'document_date': date(2023, 5, 15),
                'reduction_months': 3
            },
            {
                'employee_id': created_employees[1].id,
                'event_type': EventType.HIGHER_DEGREE.value,
                'event_date': date(2023, 8, 1),
                'description': 'الحصول على شهادة الدكتوراه',
                'document_number': 'د/456/2023',
                'document_date': date(2023, 8, 1),
                'new_academic_degree': 'دكتوراه'
            },
            {
                'employee_id': created_employees[2].id,
                'event_type': EventType.WARNING_PENALTY.value,
                'event_date': date(2023, 3, 10),
                'description': 'عقوبة إنذار للتأخير المتكرر',
                'document_number': 'ع/789/2023',
                'document_date': date(2023, 3, 10)
            },
            {
                'employee_id': created_employees[3].id,
                'event_type': EventType.UNPAID_LEAVE.value,
                'event_date': date(2023, 7, 1),
                'description': 'إجازة بدون راتب لظروف خاصة',
                'document_number': 'إ/321/2023',
                'document_date': date(2023, 6, 25),
                'start_date': date(2023, 7, 1),
                'end_date': date(2023, 9, 30)
            }
        ]
        
        for event_data in events_data:
            try:
                event = professional_event_service.create_event(event_data)
                print(f"✅ تم إنشاء الحدث المهني: {event.event_type_name} للموظف {event.employee.full_name}")
            except Exception as e:
                print(f"❌ خطأ في إنشاء الحدث: {str(e)}")
        
        print("🎉 تم إنشاء البيانات التجريبية بنجاح!")
        
    except Exception as e:
        print(f"❌ خطأ في إنشاء البيانات التجريبية: {str(e)}")
        db.session.rollback()

def initialize_database():
    """تهيئة قاعدة البيانات"""
    
    print("🔄 تهيئة قاعدة البيانات...")
    
    try:
        # إنشاء الجداول
        db.create_all()
        print("✅ تم إنشاء جداول قاعدة البيانات")
        
        # إنشاء البيانات التجريبية
        create_sample_data()
        
    except Exception as e:
        print(f"❌ خطأ في تهيئة قاعدة البيانات: {str(e)}")

def run_calculations():
    """تشغيل المحرك الحسابي لجميع الموظفين"""
    
    print("🔄 تشغيل المحرك الحسابي...")
    
    try:
        employees = Employee.query.all()
        for employee in employees:
            print(f"🔄 معالجة استحقاقات الموظف: {employee.full_name}")
            new_records = calculation_engine.process_employee_entitlements(employee)
            if new_records:
                print(f"✅ تم إضافة {len(new_records)} استحقاق جديد")
            else:
                print("ℹ️ لا توجد استحقاقات جديدة")
        
        print("🎉 تم تشغيل المحرك الحسابي بنجاح!")
        
    except Exception as e:
        print(f"❌ خطأ في تشغيل المحرك الحسابي: {str(e)}")

def print_system_info():
    """طباعة معلومات النظام"""
    
    print("\n" + "="*60)
    print("🚀 نظام أتمتة العلاوات والترفيعات الوظيفية")
    print("Employee Promotion Automation System")
    print("="*60)
    print(f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python: {sys.version}")
    print(f"📁 مجلد العمل: {os.getcwd()}")
    print("="*60)
    
    # إحصائيات النظام
    try:
        total_employees = Employee.query.count()
        total_events = ProfessionalEvent.query.count()
        total_promotions = PromotionHistory.query.count()
        
        print(f"👥 إجمالي الموظفين: {total_employees}")
        print(f"📅 إجمالي الأحداث المهنية: {total_events}")
        print(f"📈 إجمالي الترفيعات والعلاوات: {total_promotions}")
        print("="*60)
        
    except Exception as e:
        print(f"❌ خطأ في جلب الإحصائيات: {str(e)}")

def main():
    """الدالة الرئيسية"""
    
    # إنشاء التطبيق
    app = create_app()
    
    with app.app_context():
        # تهيئة قاعدة البيانات
        initialize_database()
        
        # تشغيل المحرك الحسابي
        run_calculations()
        
        # طباعة معلومات النظام
        print_system_info()
        
        print("\n🌐 بدء تشغيل الخادم...")
        print("🔗 الروابط المتاحة:")
        print("   • الصفحة الرئيسية: http://localhost:5000/")
        print("   • إدارة الموظفين: http://localhost:5000/employees/")
        print("   • الأحداث المهنية: http://localhost:5000/events/")
        print("   • التقارير: http://localhost:5000/reports/")
        print("\n⚡ للإيقاف: اضغط Ctrl+C")
        print("="*60)
        
        # تشغيل التطبيق
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=False  # تجنب إعادة التحميل المزدوج
        )

if __name__ == '__main__':
    main()

