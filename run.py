#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ملف تشغيل نظام إدارة شؤون الموظفين
Employee Management System Launcher
"""

import sys
import os

# إضافة المجلد الحالي إلى مسار Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from main import EmployeeManagementSystem
    
    if __name__ == "__main__":
        print("🚀 بدء تشغيل نظام إدارة شؤون الموظفين...")
        print("📋 Employee Management System Starting...")
        
        app = EmployeeManagementSystem()
        app.run()
        
except ImportError as e:
    print(f"❌ خطأ في استيراد المكتبات: {e}")
    print("يرجى التأكد من تثبيت جميع المتطلبات باستخدام:")
    print("pip install -r requirements.txt")
    
except Exception as e:
    print(f"❌ خطأ في تشغيل النظام: {e}")
    print("يرجى التحقق من سلامة الملفات والمتطلبات")
