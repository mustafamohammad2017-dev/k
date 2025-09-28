#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف اختبار النظام
System Test File
"""

import sqlite3
from datetime import datetime, timedelta
from calculation_engine import CalculationEngine

def create_test_data():
    """إنشاء بيانات تجريبية للاختبار"""
    
    # الاتصال بقاعدة البيانات
    conn = sqlite3.connect('employees.db')
    cursor = conn.cursor()
    
    # إنشاء الجداول إذا لم تكن موجودة
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            start_date DATE NOT NULL,
            last_allowance_date DATE NOT NULL,
            last_promotion_date DATE NOT NULL,
            promotion_tracker TEXT NOT NULL,
            academic_degree TEXT NOT NULL,
            job_category TEXT NOT NULL,
            job_title TEXT NOT NULL,
            job_grade INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS professional_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            event_date DATE NOT NULL,
            document_number TEXT,
            document_date DATE,
            description TEXT,
            impact_months INTEGER DEFAULT 0,
            start_date DATE,
            end_date DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS career_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            event_type TEXT NOT NULL,
            event_date DATE NOT NULL,
            from_grade INTEGER,
            to_grade INTEGER,
            from_stage INTEGER,
            to_stage INTEGER,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )
    ''')
    
    # حذف البيانات التجريبية السابقة
    cursor.execute("DELETE FROM employees WHERE full_name LIKE 'موظف تجريبي%'")
    
    # إضافة موظفين تجريبيين
    test_employees = [
        {
            'full_name': 'موظف تجريبي أحمد محمد علي',
            'start_date': '2020-01-01',
            'last_allowance_date': '2022-01-01',
            'last_promotion_date': '2020-01-01',
            'promotion_tracker': '2/4',
            'academic_degree': 'بكالوريوس',
            'job_category': 'إداري',
            'job_title': 'موظف إداري',
            'job_grade': 8
        },
        {
            'full_name': 'موظف تجريبي فاطمة أحمد',
            'start_date': '2018-06-01',
            'last_allowance_date': '2021-06-01',
            'last_promotion_date': '2018-06-01',
            'promotion_tracker': '3/5',
            'academic_degree': 'ماجستير',
            'job_category': 'تدريسي',
            'job_title': 'مدرس',
            'job_grade': 4
        },
        {
            'full_name': 'موظف تجريبي محمد سالم',
            'start_date': '2019-09-01',
            'last_allowance_date': '2023-09-01',
            'last_promotion_date': '2019-09-01',
            'promotion_tracker': '0/4',
            'academic_degree': 'دبلوم',
            'job_category': 'فني',
            'job_title': 'فني حاسوب',
            'job_grade': 9
        }
    ]
    
    employee_ids = []
    for emp in test_employees:
        cursor.execute('''
            INSERT INTO employees (
                full_name, start_date, last_allowance_date, last_promotion_date,
                promotion_tracker, academic_degree, job_category, job_title, job_grade
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            emp['full_name'], emp['start_date'], emp['last_allowance_date'],
            emp['last_promotion_date'], emp['promotion_tracker'], emp['academic_degree'],
            emp['job_category'], emp['job_title'], emp['job_grade']
        ))
        employee_ids.append(cursor.lastrowid)
    
    # إضافة أحداث مهنية تجريبية
    test_events = [
        {
            'employee_id': employee_ids[0],
            'event_type': 'كتاب_شكر',
            'event_date': '2022-06-01',
            'description': 'كتاب شكر وتقدير - تقليص 3 أشهر',
            'impact_months': -3
        },
        {
            'employee_id': employee_ids[1],
            'event_type': 'عقوبة_لفت_نظر',
            'event_date': '2022-03-01',
            'description': 'عقوبة لفت نظر - إضافة 3 أشهر',
            'impact_months': 3
        },
        {
            'employee_id': employee_ids[2],
            'event_type': 'اجازة_بدون_راتب',
            'event_date': '2021-01-01',
            'start_date': '2021-01-01',
            'end_date': '2021-06-01',
            'description': 'إجازة بدون راتب من 2021-01-01 إلى 2021-06-01'
        }
    ]
    
    for event in test_events:
        cursor.execute('''
            INSERT INTO professional_events (
                employee_id, event_type, event_date, description, impact_months, start_date, end_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            event['employee_id'], event['event_type'], event['event_date'],
            event['description'], event.get('impact_months', 0),
            event.get('start_date'), event.get('end_date')
        ))
    
    conn.commit()
    conn.close()
    
    print("✅ تم إنشاء البيانات التجريبية بنجاح!")
    return employee_ids

def test_calculation_engine():
    """اختبار المحرك الذكي للحسابات"""
    
    print("\n🧠 اختبار المحرك الذكي للحسابات...")
    
    # الاتصال بقاعدة البيانات
    conn = sqlite3.connect('employees.db')
    engine = CalculationEngine(conn)
    
    # جلب الموظفين التجريبيين
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name FROM employees WHERE full_name LIKE 'موظف تجريبي%'")
    employees = cursor.fetchall()
    
    for emp_id, emp_name in employees:
        print(f"\n📋 اختبار الموظف: {emp_name}")
        
        # حساب حالة الموظف
        result = engine.calculate_employee_status(emp_id)
        
        if 'error' in result:
            print(f"❌ خطأ: {result['error']}")
            continue
        
        print(f"   الدرجة الحالية: {result['current_grade']}")
        print(f"   المرحلة الحالية: {result['current_stage']}")
        print(f"   مؤشر التتبع: {result['promotion_tracker']}")
        print(f"   الاستحقاق القادم: {result['next_event_type']} بتاريخ {result['next_due_date'].strftime('%Y-%m-%d')}")
        print(f"   الخدمة الفعلية: {result['effective_service']['text']}")
        print(f"   عدد الأحداث المحسوبة: {len(result['calculated_events'])}")
        
        # عرض الأحداث المحسوبة
        if result['calculated_events']:
            print("   الأحداث المحسوبة:")
            for event in result['calculated_events']:
                print(f"     - {event['event_date'].strftime('%Y-%m-%d')}: {event['event_type']} - {event['description']}")
    
    conn.close()
    print("\n✅ انتهى اختبار المحرك الذكي!")

def test_database_integrity():
    """اختبار سلامة قاعدة البيانات"""
    
    print("\n🗄️ اختبار سلامة قاعدة البيانات...")
    
    conn = sqlite3.connect('employees.db')
    cursor = conn.cursor()
    
    # اختبار الجداول
    tables = ['employees', 'professional_events', 'career_history']
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   جدول {table}: {count} سجل")
    
    # اختبار العلاقات
    cursor.execute("""
        SELECT COUNT(*) FROM professional_events pe
        LEFT JOIN employees e ON pe.employee_id = e.id
        WHERE e.id IS NULL
    """)
    orphaned_events = cursor.fetchone()[0]
    
    if orphaned_events == 0:
        print("   ✅ جميع الأحداث المهنية مرتبطة بموظفين صحيحين")
    else:
        print(f"   ⚠️ يوجد {orphaned_events} حدث مهني غير مرتبط بموظف")
    
    conn.close()
    print("✅ انتهى اختبار قاعدة البيانات!")

def main():
    """الدالة الرئيسية للاختبار"""
    
    print("🚀 بدء اختبار نظام إدارة شؤون الموظفين")
    print("=" * 50)
    
    try:
        # إنشاء البيانات التجريبية
        employee_ids = create_test_data()
        
        # اختبار سلامة قاعدة البيانات
        test_database_integrity()
        
        # اختبار المحرك الذكي
        test_calculation_engine()
        
        print("\n" + "=" * 50)
        print("✅ تم الانتهاء من جميع الاختبارات بنجاح!")
        print("يمكنك الآن تشغيل النظام باستخدام: python run.py")
        
    except Exception as e:
        print(f"\n❌ خطأ أثناء الاختبار: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
