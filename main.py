#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام إدارة شؤون الموظفين المتكامل
Employee Management System
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
import os
import sys
from PIL import Image, ImageTk
import arabic_reshaper
from bidi.algorithm import get_display
from calculation_engine import CalculationEngine
from events_manager import EventsManager

# إعداد المظهر
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class EmployeeManagementSystem:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("نظام إدارة شؤون الموظفين")
        self.root.geometry("1400x900")
        self.root.minsize(1200, 800)
        
        # إعداد قاعدة البيانات
        self.setup_database()
        
        # إعداد المحرك الذكي ومدير الأحداث
        self.calculation_engine = CalculationEngine(self.conn)
        self.events_manager = EventsManager(self.conn, self.root)
        
        # إعداد الواجهة الرئيسية
        self.setup_main_interface()
        
    def setup_database(self):
        """إعداد قاعدة البيانات"""
        self.conn = sqlite3.connect('employees.db')
        self.cursor = self.conn.cursor()
        
        # إنشاء جدول الموظفين
        self.cursor.execute('''
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
        
        # إنشاء جدول الأحداث المهنية
        self.cursor.execute('''
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
        
        # إنشاء جدول المسار الوظيفي
        self.cursor.execute('''
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
        
        self.conn.commit()
    
    def setup_main_interface(self):
        """إعداد الواجهة الرئيسية"""
        # الشريط العلوي
        self.header_frame = ctk.CTkFrame(self.root, height=80, corner_radius=0)
        self.header_frame.pack(fill="x", padx=0, pady=0)
        self.header_frame.pack_propagate(False)
        
        # عنوان النظام
        title_label = ctk.CTkLabel(
            self.header_frame,
            text="نظام إدارة شؤون الموظفين",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="white"
        )
        title_label.pack(pady=20)
        
        # الإطار الرئيسي
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # القائمة الجانبية
        self.sidebar = ctk.CTkFrame(self.main_frame, width=300, corner_radius=10)
        self.sidebar.pack(side="right", fill="y", padx=(0, 20), pady=20)
        self.sidebar.pack_propagate(False)
        
        # منطقة المحتوى
        self.content_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.content_frame.pack(side="left", fill="both", expand=True, pady=20)
        
        # إعداد القائمة الجانبية
        self.setup_sidebar()
        
        # عرض الصفحة الرئيسية
        self.show_dashboard()
    
    def setup_sidebar(self):
        """إعداد القائمة الجانبية"""
        # عنوان القائمة
        sidebar_title = ctk.CTkLabel(
            self.sidebar,
            text="القائمة الرئيسية",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        sidebar_title.pack(pady=(20, 30))
        
        # أزرار القائمة
        buttons = [
            ("🏠 الصفحة الرئيسية", self.show_dashboard),
            ("👤 إضافة موظف جديد", self.show_add_employee),
            ("📋 قائمة الموظفين", self.show_employees_list),
            ("📊 إضافة حدث مهني", self.show_add_event),
            ("📈 التقارير", self.show_reports),
            ("⚙️ الإعدادات", self.show_settings)
        ]
        
        for text, command in buttons:
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                font=ctk.CTkFont(size=16),
                height=50,
                command=command,
                corner_radius=8
            )
            btn.pack(fill="x", padx=20, pady=10)
    
    def clear_content_frame(self):
        """مسح محتوى الإطار الرئيسي"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_dashboard(self):
        """عرض الصفحة الرئيسية"""
        self.clear_content_frame()
        
        # عنوان الصفحة
        title = ctk.CTkLabel(
            self.content_frame,
            text="لوحة التحكم الرئيسية",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        # إحصائيات سريعة
        stats_frame = ctk.CTkFrame(self.content_frame)
        stats_frame.pack(fill="x", padx=20, pady=20)
        
        # عدد الموظفين
        self.cursor.execute("SELECT COUNT(*) FROM employees")
        total_employees = self.cursor.fetchone()[0]
        
        # الموظفين المستحقين للعلاوة
        self.cursor.execute("""
            SELECT COUNT(*) FROM employees 
            WHERE date(last_allowance_date, '+12 months') <= date('now')
        """)
        due_allowance = self.cursor.fetchone()[0]
        
        # إحصائيات
        stats = [
            ("إجمالي الموظفين", total_employees, "#2196F3"),
            ("مستحقين للعلاوة", due_allowance, "#4CAF50"),
            ("الأحداث هذا الشهر", 0, "#FF9800")
        ]
        
        for i, (label, value, color) in enumerate(stats):
            stat_frame = ctk.CTkFrame(stats_frame)
            stat_frame.grid(row=0, column=i, padx=20, pady=20, sticky="ew")
            
            value_label = ctk.CTkLabel(
                stat_frame,
                text=str(value),
                font=ctk.CTkFont(size=36, weight="bold"),
                text_color=color
            )
            value_label.pack(pady=(20, 5))
            
            label_label = ctk.CTkLabel(
                stat_frame,
                text=label,
                font=ctk.CTkFont(size=14)
            )
            label_label.pack(pady=(0, 20))
        
        stats_frame.grid_columnconfigure((0, 1, 2), weight=1)
    
    def show_add_employee(self):
        """عرض صفحة إضافة موظف جديد"""
        self.clear_content_frame()
        
        # عنوان الصفحة
        title = ctk.CTkLabel(
            self.content_frame,
            text="إضافة موظف جديد",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        # إطار النموذج
        form_frame = ctk.CTkScrollableFrame(self.content_frame)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # حقول النموذج
        self.employee_form_vars = {}
        
        fields = [
            ("الاسم الرباعي واللقب", "full_name", "entry"),
            ("تاريخ المباشرة بالوظيفة", "start_date", "date"),
            ("تاريخ آخر استحقاق للعلاوة", "last_allowance_date", "date"),
            ("آخر تاريخ استحقاق للترفيع", "last_promotion_date", "date"),
            ("مؤشر تتبع العلاوة", "promotion_tracker", "combobox"),
            ("الشهادة العلمية", "academic_degree", "entry"),
            ("صنف الوظيفة", "job_category", "entry"),
            ("العنوان الوظيفي", "job_title", "entry"),
            ("الدرجة الوظيفية", "job_grade", "number")
        ]
        
        for i, (label, var_name, field_type) in enumerate(fields):
            # تسمية الحقل
            field_label = ctk.CTkLabel(
                form_frame,
                text=label,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            field_label.grid(row=i, column=0, sticky="e", padx=20, pady=10)
            
            # إنشاء الحقل حسب النوع
            if field_type == "entry":
                var = ctk.StringVar()
                widget = ctk.CTkEntry(form_frame, textvariable=var, width=300)
            elif field_type == "date":
                var = ctk.StringVar()
                widget = ctk.CTkEntry(form_frame, textvariable=var, width=300, placeholder_text="YYYY-MM-DD")
            elif field_type == "number":
                var = ctk.StringVar()
                widget = ctk.CTkEntry(form_frame, textvariable=var, width=300)
            elif field_type == "combobox":
                var = ctk.StringVar()
                values = ["4/0", "4/1", "4/2", "4/3", "5/0", "5/1", "5/2", "5/3", "5/4"]
                widget = ctk.CTkComboBox(form_frame, variable=var, values=values, width=300)
            
            widget.grid(row=i, column=1, sticky="w", padx=20, pady=10)
            self.employee_form_vars[var_name] = var
        
        # زر الحفظ
        save_btn = ctk.CTkButton(
            form_frame,
            text="💾 حفظ الموظف",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            command=self.save_employee
        )
        save_btn.grid(row=len(fields), column=0, columnspan=2, pady=30)
    
    def save_employee(self):
        """حفظ بيانات الموظف الجديد"""
        try:
            # التحقق من صحة البيانات
            data = {}
            for field, var in self.employee_form_vars.items():
                value = var.get().strip()
                if not value:
                    messagebox.showerror("خطأ", f"يرجى ملء حقل {field}")
                    return
                data[field] = value
            
            # إدراج البيانات في قاعدة البيانات
            self.cursor.execute('''
                INSERT INTO employees (
                    full_name, start_date, last_allowance_date, last_promotion_date,
                    promotion_tracker, academic_degree, job_category, job_title, job_grade
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['full_name'], data['start_date'], data['last_allowance_date'],
                data['last_promotion_date'], data['promotion_tracker'], data['academic_degree'],
                data['job_category'], data['job_title'], int(data['job_grade'])
            ))
            
            self.conn.commit()
            messagebox.showinfo("نجح", "تم حفظ بيانات الموظف بنجاح!")
            
            # مسح النموذج
            for var in self.employee_form_vars.values():
                var.set("")
                
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء حفظ البيانات: {str(e)}")
    
    def show_employees_list(self):
        """عرض قائمة الموظفين"""
        self.clear_content_frame()
        
        # عنوان الصفحة
        title = ctk.CTkLabel(
            self.content_frame,
            text="قائمة الموظفين",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        # إطار البحث والفلترة
        search_frame = ctk.CTkFrame(self.content_frame)
        search_frame.pack(fill="x", padx=20, pady=10)
        
        # حقل البحث
        search_label = ctk.CTkLabel(search_frame, text="البحث:")
        search_label.pack(side="right", padx=10, pady=10)
        
        self.search_var = ctk.StringVar()
        search_entry = ctk.CTkEntry(search_frame, textvariable=self.search_var, width=200)
        search_entry.pack(side="right", padx=10, pady=10)
        
        # زر البحث
        search_btn = ctk.CTkButton(
            search_frame,
            text="🔍 بحث",
            command=self.search_employees,
            width=100
        )
        search_btn.pack(side="right", padx=10, pady=10)
        
        # جدول الموظفين
        self.employees_tree = ttk.Treeview(
            self.content_frame,
            columns=("name", "category", "title", "start_date", "service"),
            show="headings",
            height=15
        )
        
        # تعريف الأعمدة
        self.employees_tree.heading("name", text="الاسم")
        self.employees_tree.heading("category", text="صنف الوظيفة")
        self.employees_tree.heading("title", text="العنوان الوظيفي")
        self.employees_tree.heading("start_date", text="تاريخ المباشرة")
        self.employees_tree.heading("service", text="الخدمة الفعلية")
        
        # تحديد عرض الأعمدة
        self.employees_tree.column("name", width=200)
        self.employees_tree.column("category", width=150)
        self.employees_tree.column("title", width=150)
        self.employees_tree.column("start_date", width=120)
        self.employees_tree.column("service", width=120)
        
        self.employees_tree.pack(fill="both", expand=True, padx=20, pady=10)
        
        # شريط التمرير
        scrollbar = ttk.Scrollbar(self.employees_tree, orient="vertical", command=self.employees_tree.yview)
        self.employees_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="left", fill="y")
        
        # ربط النقر المزدوج لفتح ملف الموظف
        self.employees_tree.bind("<Double-1>", self.open_employee_profile)
        
        # تحميل بيانات الموظفين
        self.load_employees_data()
    
    def load_employees_data(self):
        """تحميل بيانات الموظفين"""
        # مسح البيانات الحالية
        for item in self.employees_tree.get_children():
            self.employees_tree.delete(item)
        
        # جلب البيانات من قاعدة البيانات
        self.cursor.execute("""
            SELECT id, full_name, job_category, job_title, start_date
            FROM employees
            ORDER BY full_name
        """)
        
        employees = self.cursor.fetchall()
        
        for emp in employees:
            emp_id, name, category, title, start_date = emp
            
            # حساب الخدمة الفعلية
            start = datetime.strptime(start_date, "%Y-%m-%d")
            service_days = (datetime.now() - start).days
            service_years = service_days // 365
            service_months = (service_days % 365) // 30
            service_text = f"{service_years} سنة، {service_months} شهر"
            
            self.employees_tree.insert("", "end", values=(name, category, title, start_date, service_text))
    
    def search_employees(self):
        """البحث في الموظفين"""
        search_term = self.search_var.get().strip()
        
        # مسح البيانات الحالية
        for item in self.employees_tree.get_children():
            self.employees_tree.delete(item)
        
        if search_term:
            self.cursor.execute("""
                SELECT id, full_name, job_category, job_title, start_date
                FROM employees
                WHERE full_name LIKE ? OR job_category LIKE ? OR job_title LIKE ?
                ORDER BY full_name
            """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
        else:
            self.cursor.execute("""
                SELECT id, full_name, job_category, job_title, start_date
                FROM employees
                ORDER BY full_name
            """)
        
        employees = self.cursor.fetchall()
        
        for emp in employees:
            emp_id, name, category, title, start_date = emp
            
            # حساب الخدمة الفعلية
            start = datetime.strptime(start_date, "%Y-%m-%d")
            service_days = (datetime.now() - start).days
            service_years = service_days // 365
            service_months = (service_days % 365) // 30
            service_text = f"{service_years} سنة، {service_months} شهر"
            
            self.employees_tree.insert("", "end", values=(name, category, title, start_date, service_text))
    
    def open_employee_profile(self, event):
        """فتح ملف الموظف"""
        selection = self.employees_tree.selection()
        if selection:
            item = self.employees_tree.item(selection[0])
            employee_name = item['values'][0]
            
            # البحث عن الموظف في قاعدة البيانات
            self.cursor.execute("SELECT * FROM employees WHERE full_name = ?", (employee_name,))
            employee = self.cursor.fetchone()
            
            if employee:
                self.show_employee_profile(employee)
    
    def show_employee_profile(self, employee):
        """عرض ملف الموظف"""
        self.clear_content_frame()
        
        # معلومات الموظف
        emp_id, full_name, start_date, last_allowance_date, last_promotion_date, promotion_tracker, academic_degree, job_category, job_title, job_grade, created_at, updated_at = employee
        
        # تطبيق المحرك الذكي لحساب الحالة الحالية
        calculation_result = self.calculation_engine.calculate_employee_status(emp_id)
        
        # عنوان الصفحة
        title = ctk.CTkLabel(
            self.content_frame,
            text=f"ملف الموظف: {full_name}",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        # قسم الرأس
        header_frame = ctk.CTkFrame(self.content_frame)
        header_frame.pack(fill="x", padx=20, pady=10)
        
        # صورة الموظف (افتراضية)
        photo_frame = ctk.CTkFrame(header_frame, width=150, height=150)
        photo_frame.pack(side="right", padx=20, pady=20)
        photo_frame.pack_propagate(False)
        
        photo_label = ctk.CTkLabel(photo_frame, text="📷\nصورة الموظف", font=ctk.CTkFont(size=16))
        photo_label.pack(expand=True)
        
        # معلومات أساسية
        info_frame = ctk.CTkFrame(header_frame)
        info_frame.pack(side="left", fill="both", expand=True, padx=20, pady=20)
        
        info_labels = [
            ("الاسم:", full_name),
            ("صنف الوظيفة:", job_category),
            ("العنوان الوظيفي:", job_title),
            ("الشهادة:", academic_degree),
            ("الدرجة الحالية:", str(job_grade))
        ]
        
        for i, (label, value) in enumerate(info_labels):
            label_widget = ctk.CTkLabel(info_frame, text=label, font=ctk.CTkFont(size=14, weight="bold"))
            label_widget.grid(row=i, column=0, sticky="e", padx=10, pady=5)
            
            value_widget = ctk.CTkLabel(info_frame, text=value, font=ctk.CTkFont(size=14))
            value_widget.grid(row=i, column=1, sticky="w", padx=10, pady=5)
        
        # المؤشرات الرئيسية
        metrics_frame = ctk.CTkFrame(self.content_frame)
        metrics_frame.pack(fill="x", padx=20, pady=10)
        
        # استخدام النتائج من المحرك الذكي
        if 'error' not in calculation_result:
            current_grade = calculation_result['current_grade']
            current_stage = calculation_result['current_stage']
            next_due_date = calculation_result['next_due_date'].strftime("%Y-%m-%d")
            next_event_type = calculation_result['next_event_type']
            effective_service = calculation_result['effective_service']['text']
            
            metrics = [
                ("الدرجة والمرحلة الحالية", f"الدرجة: {current_grade}\nالمرحلة: {current_stage}", "#2196F3"),
                ("الاستحقاق القادم", f"{next_event_type}\nبتاريخ: {next_due_date}", "#4CAF50"),
                ("الخدمة الفعلية", effective_service, "#FF9800")
            ]
        else:
            # في حالة وجود خطأ، استخدم الحسابات البسيطة
            start = datetime.strptime(start_date, "%Y-%m-%d")
            service_days = (datetime.now() - start).days
            service_years = service_days // 365
            service_months = (service_days % 365) // 30
            service_text = f"{service_years} سنة، {service_months} شهر"
            
            last_allowance = datetime.strptime(last_allowance_date, "%Y-%m-%d")
            next_due = last_allowance + timedelta(days=365)
            next_due_text = next_due.strftime("%Y-%m-%d")
            
            metrics = [
                ("الدرجة والمرحلة الحالية", f"الدرجة: {job_grade}\nالمرحلة: {promotion_tracker}", "#2196F3"),
                ("الاستحقاق القادم", f"علاوة\nبتاريخ: {next_due_text}", "#4CAF50"),
                ("الخدمة الفعلية", service_text, "#FF9800")
            ]
        
        for i, (title, value, color) in enumerate(metrics):
            metric_frame = ctk.CTkFrame(metrics_frame)
            metric_frame.grid(row=0, column=i, padx=20, pady=20, sticky="ew")
            
            title_label = ctk.CTkLabel(
                metric_frame,
                text=title,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            title_label.pack(pady=(20, 5))
            
            value_label = ctk.CTkLabel(
                metric_frame,
                text=value,
                font=ctk.CTkFont(size=16),
                text_color=color
            )
            value_label.pack(pady=(0, 20))
        
        metrics_frame.grid_columnconfigure((0, 1, 2), weight=1)
        
        # التبويبات
        tabview = ctk.CTkTabview(self.content_frame)
        tabview.pack(fill="both", expand=True, padx=20, pady=20)
        
        # تبويب المسار الوظيفي
        career_tab = tabview.add("المسار الوظيفي")
        career_label = ctk.CTkLabel(career_tab, text="سجل العلاوات والترفيعات", font=ctk.CTkFont(size=16, weight="bold"))
        career_label.pack(pady=20)
        
        # عرض الأحداث المحسوبة من المحرك الذكي
        if 'error' not in calculation_result and calculation_result['calculated_events']:
            career_tree = ttk.Treeview(
                career_tab,
                columns=("date", "type", "from_grade", "to_grade", "description"),
                show="headings",
                height=12
            )
            
            career_tree.heading("date", text="التاريخ")
            career_tree.heading("type", text="نوع الحدث")
            career_tree.heading("from_grade", text="من")
            career_tree.heading("to_grade", text="إلى")
            career_tree.heading("description", text="الوصف")
            
            career_tree.column("date", width=100)
            career_tree.column("type", width=80)
            career_tree.column("from_grade", width=80)
            career_tree.column("to_grade", width=80)
            career_tree.column("description", width=300)
            
            career_tree.pack(fill="both", expand=True, padx=20, pady=10)
            
            # إدراج الأحداث المحسوبة
            for event in calculation_result['calculated_events']:
                career_tree.insert("", "end", values=(
                    event['event_date'].strftime("%Y-%m-%d"),
                    event['event_type'],
                    f"الدرجة {event['from_grade']} المرحلة {event['from_stage']}",
                    f"الدرجة {event['to_grade']} المرحلة {event['to_stage']}",
                    event['description']
                ))
        else:
            no_career_label = ctk.CTkLabel(career_tab, text="لا توجد أحداث وظيفية محسوبة", font=ctk.CTkFont(size=14))
            no_career_label.pack(pady=50)
        
        # تبويب الأحداث المهنية
        events_tab = tabview.add("الأحداث المهنية")
        events_label = ctk.CTkLabel(events_tab, text="سجل الأحداث المهنية", font=ctk.CTkFont(size=16, weight="bold"))
        events_label.pack(pady=20)
        
        # جلب الأحداث المهنية
        self.cursor.execute("""
            SELECT event_type, event_date, description, notes
            FROM professional_events
            WHERE employee_id = ?
            ORDER BY event_date DESC
        """, (emp_id,))
        
        events = self.cursor.fetchall()
        
        if events:
            events_tree = ttk.Treeview(
                events_tab,
                columns=("type", "date", "description"),
                show="headings",
                height=10
            )
            
            events_tree.heading("type", text="نوع الحدث")
            events_tree.heading("date", text="التاريخ")
            events_tree.heading("description", text="الوصف")
            
            events_tree.pack(fill="both", expand=True, padx=20, pady=10)
            
            for event in events:
                events_tree.insert("", "end", values=event[:3])
        else:
            no_events_label = ctk.CTkLabel(events_tab, text="لا توجد أحداث مهنية مسجلة", font=ctk.CTkFont(size=14))
            no_events_label.pack(pady=50)
    
    def show_add_event(self):
        """عرض صفحة إضافة حدث مهني"""
        self.clear_content_frame()
        self.events_manager.show_add_event_interface(self.content_frame)
    
    def show_reports(self):
        """عرض صفحة التقارير"""
        self.clear_content_frame()
        
        title = ctk.CTkLabel(
            self.content_frame,
            text="التقارير",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        message = ctk.CTkLabel(
            self.content_frame,
            text="هذه الصفحة قيد التطوير...\nسيتم إضافة التقارير والإحصائيات قريباً",
            font=ctk.CTkFont(size=16)
        )
        message.pack(pady=100)
    
    def show_settings(self):
        """عرض صفحة الإعدادات"""
        self.clear_content_frame()
        
        title = ctk.CTkLabel(
            self.content_frame,
            text="الإعدادات",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        message = ctk.CTkLabel(
            self.content_frame,
            text="هذه الصفحة قيد التطوير...\nسيتم إضافة إعدادات النظام قريباً",
            font=ctk.CTkFont(size=16)
        )
        message.pack(pady=100)
    
    def run(self):
        """تشغيل التطبيق"""
        self.root.mainloop()
    
    def __del__(self):
        """إغلاق اتصال قاعدة البيانات"""
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    app = EmployeeManagementSystem()
    app.run()
