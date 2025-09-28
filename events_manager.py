#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
وحدة إدارة الأحداث المهنية
Professional Events Manager
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import sqlite3
from typing import List, Dict

class EventsManager:
    """مدير الأحداث المهنية"""
    
    def __init__(self, db_connection, parent_window):
        self.conn = db_connection
        self.cursor = db_connection.cursor()
        self.parent = parent_window
        
        # أنواع الأحداث وتأثيرها
        self.event_types = {
            'كتاب_شكر': {
                'name': 'كتاب شكر وتقدير',
                'impact_type': 'positive',
                'reduction_options': [1, 2, 3, 4, 5, 6]
            },
            'شهادة_عليا': {
                'name': 'الحصول على شهادة أعلى',
                'impact_type': 'positive',
                'reduction_months': 12
            },
            'عقوبة_لفت_نظر': {
                'name': 'عقوبة لفت نظر',
                'impact_type': 'negative',
                'additional_months': 3
            },
            'عقوبة_انذار': {
                'name': 'عقوبة إنذار',
                'impact_type': 'negative',
                'additional_months': 6
            },
            'عقوبة_توبيخ': {
                'name': 'عقوبة توبيخ',
                'impact_type': 'negative',
                'additional_months': 12
            },
            'اجازة_بدون_راتب': {
                'name': 'إجازة بدون راتب',
                'impact_type': 'freeze',
                'requires_dates': True
            },
            'اجازة_رعاية_معاقين': {
                'name': 'إجازة رعاية المعاقين',
                'impact_type': 'freeze',
                'requires_dates': True
            },
            'اجازة_خمس_سنوات': {
                'name': 'إجازة الخمس سنوات',
                'impact_type': 'freeze',
                'requires_dates': True
            },
            'حدث_مخصص': {
                'name': 'حدث مخصص',
                'impact_type': 'custom',
                'requires_manual_input': True
            }
        }
    
    def show_add_event_interface(self, content_frame):
        """عرض واجهة إضافة حدث مهني"""
        
        # عنوان الصفحة
        title = ctk.CTkLabel(
            content_frame,
            text="إضافة حدث مهني",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=20)
        
        # إطار النموذج
        form_frame = ctk.CTkScrollableFrame(content_frame)
        form_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # متغيرات النموذج
        self.event_form_vars = {}
        
        # 1. تحديد الموظفين
        self.setup_employee_selection(form_frame)
        
        # 2. نوع الحدث
        self.setup_event_type_selection(form_frame)
        
        # 3. الحقول المشتركة
        self.setup_common_fields(form_frame)
        
        # 4. الحقول الديناميكية
        self.dynamic_fields_frame = ctk.CTkFrame(form_frame)
        self.dynamic_fields_frame.pack(fill="x", padx=20, pady=20)
        
        # 5. زر الحفظ
        save_btn = ctk.CTkButton(
            form_frame,
            text="💾 حفظ الحدث",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50,
            command=self.save_event
        )
        save_btn.pack(pady=30)
    
    def setup_employee_selection(self, parent):
        """إعداد قسم تحديد الموظفين"""
        
        # عنوان القسم
        section_title = ctk.CTkLabel(
            parent,
            text="تحديد الموظفين",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        section_title.pack(pady=(20, 10))
        
        # إطار تحديد الموظفين
        employees_frame = ctk.CTkFrame(parent)
        employees_frame.pack(fill="x", padx=20, pady=10)
        
        # زر تحديد الكل
        self.select_all_var = ctk.BooleanVar()
        select_all_cb = ctk.CTkCheckBox(
            employees_frame,
            text="تحديد جميع الموظفين",
            variable=self.select_all_var,
            command=self.toggle_select_all,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        select_all_cb.pack(pady=10)
        
        # قائمة الموظفين
        self.employees_frame = ctk.CTkScrollableFrame(employees_frame, height=200)
        self.employees_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # تحميل قائمة الموظفين
        self.load_employees_list()
    
    def load_employees_list(self):
        """تحميل قائمة الموظفين"""
        
        # جلب الموظفين من قاعدة البيانات
        self.cursor.execute("""
            SELECT id, full_name, job_category, job_title
            FROM employees
            ORDER BY job_category, full_name
        """)
        
        employees = self.cursor.fetchall()
        self.employee_checkboxes = {}
        
        current_category = None
        for emp_id, name, category, title in employees:
            
            # عرض عنوان الصنف الوظيفي
            if category != current_category:
                category_label = ctk.CTkLabel(
                    self.employees_frame,
                    text=f"--- {category} ---",
                    font=ctk.CTkFont(size=14, weight="bold")
                )
                category_label.pack(pady=(10, 5))
                current_category = category
            
            # مربع تحديد الموظف
            var = ctk.BooleanVar()
            checkbox = ctk.CTkCheckBox(
                self.employees_frame,
                text=f"{name} - {title}",
                variable=var,
                font=ctk.CTkFont(size=12)
            )
            checkbox.pack(anchor="w", padx=20, pady=2)
            
            self.employee_checkboxes[emp_id] = {
                'var': var,
                'name': name,
                'category': category
            }
    
    def toggle_select_all(self):
        """تبديل تحديد جميع الموظفين"""
        select_all = self.select_all_var.get()
        
        for emp_data in self.employee_checkboxes.values():
            emp_data['var'].set(select_all)
    
    def setup_event_type_selection(self, parent):
        """إعداد قسم اختيار نوع الحدث"""
        
        # عنوان القسم
        section_title = ctk.CTkLabel(
            parent,
            text="نوع الحدث",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        section_title.pack(pady=(20, 10))
        
        # قائمة منسدلة لنوع الحدث
        self.event_type_var = ctk.StringVar()
        event_type_combo = ctk.CTkComboBox(
            parent,
            variable=self.event_type_var,
            values=[info['name'] for info in self.event_types.values()],
            command=self.on_event_type_change,
            width=400,
            font=ctk.CTkFont(size=14)
        )
        event_type_combo.pack(pady=10)
        
        self.event_form_vars['event_type'] = self.event_type_var
    
    def setup_common_fields(self, parent):
        """إعداد الحقول المشتركة"""
        
        # عنوان القسم
        section_title = ctk.CTkLabel(
            parent,
            text="معلومات الحدث",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        section_title.pack(pady=(20, 10))
        
        # إطار الحقول المشتركة
        common_frame = ctk.CTkFrame(parent)
        common_frame.pack(fill="x", padx=20, pady=10)
        
        # الحقول المشتركة
        common_fields = [
            ("رقم الكتاب الرسمي", "document_number", "entry"),
            ("تاريخ الكتاب الرسمي", "document_date", "date"),
            ("ملاحظات", "notes", "text")
        ]
        
        for i, (label, var_name, field_type) in enumerate(common_fields):
            # تسمية الحقل
            field_label = ctk.CTkLabel(
                common_frame,
                text=label,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            field_label.grid(row=i, column=0, sticky="e", padx=20, pady=10)
            
            # إنشاء الحقل
            if field_type == "entry":
                var = ctk.StringVar()
                widget = ctk.CTkEntry(common_frame, textvariable=var, width=300)
            elif field_type == "date":
                var = ctk.StringVar()
                widget = ctk.CTkEntry(common_frame, textvariable=var, width=300, placeholder_text="YYYY-MM-DD")
            elif field_type == "text":
                var = ctk.StringVar()
                widget = ctk.CTkTextbox(common_frame, width=300, height=80)
            
            widget.grid(row=i, column=1, sticky="w", padx=20, pady=10)
            self.event_form_vars[var_name] = var
    
    def on_event_type_change(self, selected_type):
        """عند تغيير نوع الحدث"""
        
        # مسح الحقول الديناميكية
        for widget in self.dynamic_fields_frame.winfo_children():
            widget.destroy()
        
        # العثور على نوع الحدث
        event_key = None
        for key, info in self.event_types.items():
            if info['name'] == selected_type:
                event_key = key
                break
        
        if not event_key:
            return
        
        event_info = self.event_types[event_key]
        
        # إضافة الحقول الخاصة بنوع الحدث
        if event_key == 'كتاب_شكر':
            self.setup_commendation_fields()
        elif event_key == 'شهادة_عليا':
            self.setup_degree_fields()
        elif event_info['impact_type'] == 'freeze':
            self.setup_freeze_fields()
        elif event_key == 'حدث_مخصص':
            self.setup_custom_fields()
    
    def setup_commendation_fields(self):
        """إعداد حقول كتاب الشكر"""
        
        title = ctk.CTkLabel(
            self.dynamic_fields_frame,
            text="تفاصيل كتاب الشكر",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(pady=10)
        
        # مدة التقليص
        reduction_label = ctk.CTkLabel(
            self.dynamic_fields_frame,
            text="مدة التقليص (بالأشهر):",
            font=ctk.CTkFont(size=14)
        )
        reduction_label.pack(pady=5)
        
        self.reduction_var = ctk.StringVar()
        reduction_combo = ctk.CTkComboBox(
            self.dynamic_fields_frame,
            variable=self.reduction_var,
            values=["1", "2", "3", "4", "5", "6"],
            width=200
        )
        reduction_combo.pack(pady=5)
        
        self.event_form_vars['reduction_months'] = self.reduction_var
    
    def setup_degree_fields(self):
        """إعداد حقول الشهادة العليا"""
        
        title = ctk.CTkLabel(
            self.dynamic_fields_frame,
            text="تفاصيل الشهادة الجديدة",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(pady=10)
        
        # الحقول الجديدة
        degree_fields = [
            ("صنف الموظف الجديد", "new_job_category"),
            ("العنوان الوظيفي الجديد", "new_job_title"),
            ("الشهادة العلمية الجديدة", "new_academic_degree")
        ]
        
        for label, var_name in degree_fields:
            field_label = ctk.CTkLabel(
                self.dynamic_fields_frame,
                text=label + ":",
                font=ctk.CTkFont(size=14)
            )
            field_label.pack(pady=5)
            
            var = ctk.StringVar()
            entry = ctk.CTkEntry(
                self.dynamic_fields_frame,
                textvariable=var,
                width=300
            )
            entry.pack(pady=5)
            
            self.event_form_vars[var_name] = var
    
    def setup_freeze_fields(self):
        """إعداد حقول الإجازات"""
        
        title = ctk.CTkLabel(
            self.dynamic_fields_frame,
            text="فترة الإجازة",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(pady=10)
        
        # تاريخ الانفكاك
        start_label = ctk.CTkLabel(
            self.dynamic_fields_frame,
            text="تاريخ الانفكاك:",
            font=ctk.CTkFont(size=14)
        )
        start_label.pack(pady=5)
        
        self.start_date_var = ctk.StringVar()
        start_entry = ctk.CTkEntry(
            self.dynamic_fields_frame,
            textvariable=self.start_date_var,
            width=200,
            placeholder_text="YYYY-MM-DD"
        )
        start_entry.pack(pady=5)
        
        # تاريخ المباشرة
        end_label = ctk.CTkLabel(
            self.dynamic_fields_frame,
            text="تاريخ المباشرة:",
            font=ctk.CTkFont(size=14)
        )
        end_label.pack(pady=5)
        
        self.end_date_var = ctk.StringVar()
        end_entry = ctk.CTkEntry(
            self.dynamic_fields_frame,
            textvariable=self.end_date_var,
            width=200,
            placeholder_text="YYYY-MM-DD"
        )
        end_entry.pack(pady=5)
        
        self.event_form_vars['start_date'] = self.start_date_var
        self.event_form_vars['end_date'] = self.end_date_var
    
    def setup_custom_fields(self):
        """إعداد حقول الحدث المخصص"""
        
        title = ctk.CTkLabel(
            self.dynamic_fields_frame,
            text="تفاصيل الحدث المخصص",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(pady=10)
        
        # نوع التعديل
        adjustment_label = ctk.CTkLabel(
            self.dynamic_fields_frame,
            text="نوع التعديل:",
            font=ctk.CTkFont(size=14)
        )
        adjustment_label.pack(pady=5)
        
        self.adjustment_type_var = ctk.StringVar()
        adjustment_combo = ctk.CTkComboBox(
            self.dynamic_fields_frame,
            variable=self.adjustment_type_var,
            values=["إضافة مدة", "طرح مدة"],
            width=200
        )
        adjustment_combo.pack(pady=5)
        
        # عدد الشهور
        months_label = ctk.CTkLabel(
            self.dynamic_fields_frame,
            text="عدد الشهور:",
            font=ctk.CTkFont(size=14)
        )
        months_label.pack(pady=5)
        
        self.custom_months_var = ctk.StringVar()
        months_entry = ctk.CTkEntry(
            self.dynamic_fields_frame,
            textvariable=self.custom_months_var,
            width=200
        )
        months_entry.pack(pady=5)
        
        self.event_form_vars['adjustment_type'] = self.adjustment_type_var
        self.event_form_vars['custom_months'] = self.custom_months_var
    
    def save_event(self):
        """حفظ الحدث المهني"""
        
        try:
            # التحقق من تحديد الموظفين
            selected_employees = []
            for emp_id, emp_data in self.employee_checkboxes.items():
                if emp_data['var'].get():
                    selected_employees.append(emp_id)
            
            if not selected_employees:
                messagebox.showerror("خطأ", "يرجى تحديد موظف واحد على الأقل")
                return
            
            # التحقق من نوع الحدث
            event_type_name = self.event_type_var.get()
            if not event_type_name:
                messagebox.showerror("خطأ", "يرجى اختيار نوع الحدث")
                return
            
            # العثور على مفتاح نوع الحدث
            event_key = None
            for key, info in self.event_types.items():
                if info['name'] == event_type_name:
                    event_key = key
                    break
            
            # حفظ الحدث لكل موظف محدد
            for emp_id in selected_employees:
                self.save_single_event(emp_id, event_key)
            
            messagebox.showinfo("نجح", f"تم حفظ الحدث لـ {len(selected_employees)} موظف بنجاح!")
            
            # مسح النموذج
            self.clear_form()
            
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء حفظ الحدث: {str(e)}")
    
    def save_single_event(self, employee_id: int, event_key: str):
        """حفظ حدث واحد لموظف محدد"""
        
        # جمع البيانات الأساسية
        document_number = self.event_form_vars.get('document_number', ctk.StringVar()).get()
        document_date = self.event_form_vars.get('document_date', ctk.StringVar()).get()
        notes = self.event_form_vars.get('notes', ctk.StringVar()).get()
        
        # تحديد تأثير الحدث
        impact_months = 0
        start_date = None
        end_date = None
        description = self.event_types[event_key]['name']
        
        if event_key == 'كتاب_شكر':
            impact_months = -int(self.event_form_vars.get('reduction_months', ctk.StringVar()).get() or 0)
            description += f" - تقليص {abs(impact_months)} شهر"
            
        elif event_key == 'شهادة_عليا':
            impact_months = -12
            description += " - تقليص 12 شهر"
            
            # تحديث بيانات الموظف
            new_category = self.event_form_vars.get('new_job_category', ctk.StringVar()).get()
            new_title = self.event_form_vars.get('new_job_title', ctk.StringVar()).get()
            new_degree = self.event_form_vars.get('new_academic_degree', ctk.StringVar()).get()
            
            if new_category or new_title or new_degree:
                self.update_employee_info(employee_id, new_category, new_title, new_degree)
        
        elif event_key in ['عقوبة_لفت_نظر', 'عقوبة_انذار', 'عقوبة_توبيخ']:
            impact_months = self.event_types[event_key]['additional_months']
            description += f" - إضافة {impact_months} شهر"
        
        elif event_key in ['اجازة_بدون_راتب', 'اجازة_رعاية_معاقين', 'اجازة_خمس_سنوات']:
            start_date = self.event_form_vars.get('start_date', ctk.StringVar()).get()
            end_date = self.event_form_vars.get('end_date', ctk.StringVar()).get()
            description += f" من {start_date} إلى {end_date}"
        
        elif event_key == 'حدث_مخصص':
            adjustment_type = self.event_form_vars.get('adjustment_type', ctk.StringVar()).get()
            custom_months = int(self.event_form_vars.get('custom_months', ctk.StringVar()).get() or 0)
            
            if adjustment_type == "طرح مدة":
                impact_months = -custom_months
            else:
                impact_months = custom_months
            
            description += f" - {adjustment_type} {abs(impact_months)} شهر"
        
        # إدراج الحدث في قاعدة البيانات
        self.cursor.execute("""
            INSERT INTO professional_events (
                employee_id, event_type, event_date, document_number, document_date,
                description, impact_months, start_date, end_date, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            employee_id, event_key, datetime.now().strftime("%Y-%m-%d"),
            document_number, document_date, description, impact_months,
            start_date, end_date, notes
        ))
        
        self.conn.commit()
    
    def update_employee_info(self, employee_id: int, new_category: str, new_title: str, new_degree: str):
        """تحديث معلومات الموظف"""
        
        update_fields = []
        update_values = []
        
        if new_category:
            update_fields.append("job_category = ?")
            update_values.append(new_category)
        
        if new_title:
            update_fields.append("job_title = ?")
            update_values.append(new_title)
        
        if new_degree:
            update_fields.append("academic_degree = ?")
            update_values.append(new_degree)
        
        if update_fields:
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            update_values.append(employee_id)
            
            query = f"UPDATE employees SET {', '.join(update_fields)} WHERE id = ?"
            self.cursor.execute(query, update_values)
    
    def clear_form(self):
        """مسح النموذج"""
        
        # إلغاء تحديد جميع الموظفين
        self.select_all_var.set(False)
        for emp_data in self.employee_checkboxes.values():
            emp_data['var'].set(False)
        
        # مسح الحقول
        for var in self.event_form_vars.values():
            if hasattr(var, 'set'):
                var.set("")
        
        # مسح الحقول الديناميكية
        for widget in self.dynamic_fields_frame.winfo_children():
            widget.destroy()
