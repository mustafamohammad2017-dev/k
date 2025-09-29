// نظام أتمتة العلاوات والترفيعات - JavaScript الرئيسي

$(document).ready(function() {
    // تهيئة Moment.js للعربية
    moment.locale('ar');
    
    // تهيئة التلميحات
    initializeTooltips();
    
    // تهيئة النماذج
    initializeForms();
    
    // تهيئة الجداول
    initializeTables();
    
    // تهيئة البحث
    initializeSearch();
    
    // تهيئة التحديث التلقائي للتواريخ
    updateRelativeDates();
    setInterval(updateRelativeDates, 60000); // كل دقيقة
});

// تهيئة التلميحات
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// تهيئة النماذج
function initializeForms() {
    // التحقق من صحة النماذج
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // تنسيق حقول التاريخ
    $('input[type="date"]').each(function() {
        if (!$(this).val()) {
            $(this).addClass('empty-date');
        }
    });
    
    $('input[type="date"]').on('change', function() {
        if ($(this).val()) {
            $(this).removeClass('empty-date');
        } else {
            $(this).addClass('empty-date');
        }
    });
}

// تهيئة الجداول
function initializeTables() {
    // إضافة فئات CSS للجداول
    $('.table').addClass('table-hover');
    
    // تحديث عدد النتائج
    updateResultsCount();
}

// تهيئة البحث
function initializeSearch() {
    // البحث المباشر
    let searchTimeout;
    $('.search-input').on('input', function() {
        clearTimeout(searchTimeout);
        const searchTerm = $(this).val();
        const targetTable = $(this).data('target');
        
        searchTimeout = setTimeout(function() {
            performSearch(searchTerm, targetTable);
        }, 300);
    });
    
    // البحث في الموظفين للأحداث المهنية
    $('#employee-search').on('input', function() {
        const searchTerm = $(this).val().toLowerCase();
        $('.employee-checkbox-item').each(function() {
            const employeeName = $(this).find('label').text().toLowerCase();
            if (employeeName.includes(searchTerm)) {
                $(this).show();
            } else {
                $(this).hide();
            }
        });
    });
}

// تنفيذ البحث
function performSearch(searchTerm, targetTable) {
    if (!targetTable) return;
    
    const table = $(targetTable);
    const rows = table.find('tbody tr');
    
    if (!searchTerm) {
        rows.show();
        updateResultsCount();
        return;
    }
    
    rows.each(function() {
        const rowText = $(this).text().toLowerCase();
        if (rowText.includes(searchTerm.toLowerCase())) {
            $(this).show();
        } else {
            $(this).hide();
        }
    });
    
    updateResultsCount();
}

// تحديث عدد النتائج
function updateResultsCount() {
    $('.results-count').each(function() {
        const targetTable = $(this).data('target');
        if (targetTable) {
            const visibleRows = $(targetTable + ' tbody tr:visible').length;
            $(this).text(visibleRows);
        }
    });
}

// تحديث التواريخ النسبية
function updateRelativeDates() {
    $('.relative-date').each(function() {
        const date = $(this).data('date');
        if (date) {
            const relativeDateText = moment(date).fromNow();
            $(this).text(relativeDateText);
        }
    });
    
    $('.days-remaining').each(function() {
        const date = $(this).data('date');
        if (date) {
            const daysRemaining = moment(date).diff(moment(), 'days');
            $(this).text(daysRemaining + ' يوم');
            
            // تحديث الألوان حسب الأيام المتبقية
            $(this).removeClass('badge-danger badge-warning badge-info badge-success');
            if (daysRemaining < 0) {
                $(this).addClass('badge-danger');
            } else if (daysRemaining <= 7) {
                $(this).addClass('badge-warning');
            } else if (daysRemaining <= 30) {
                $(this).addClass('badge-info');
            } else {
                $(this).addClass('badge-success');
            }
        }
    });
}

// وظائف الأحداث المهنية
const EventManager = {
    // تغيير نوع الحدث
    onEventTypeChange: function(eventType) {
        // إخفاء جميع الأقسام الخاصة
        $('.event-specific-section').hide();
        
        // إظهار القسم المناسب
        switch(eventType) {
            case 'commendation':
                $('#commendation-section').show();
                break;
            case 'higher_degree':
                $('#higher-degree-section').show();
                break;
            case 'unpaid_leave':
            case 'disability_leave':
            case 'five_year_leave':
            case 'maternity_leave':
                $('#leave-section').show();
                break;
            case 'custom':
                $('#custom-section').show();
                break;
        }
    },
    
    // تحديد/إلغاء تحديد جميع الموظفين
    toggleAllEmployees: function(checked) {
        $('.employee-checkbox').prop('checked', checked);
        this.updateSelectedCount();
    },
    
    // تحديد/إلغاء تحديد موظفي صنف معين
    toggleCategoryEmployees: function(category, checked) {
        $(`.employee-checkbox[data-category="${category}"]`).prop('checked', checked);
        this.updateSelectedCount();
    },
    
    // تحديث عدد الموظفين المحددين
    updateSelectedCount: function() {
        const selectedCount = $('.employee-checkbox:checked').length;
        $('#selected-employees-count').text(selectedCount);
        
        if (selectedCount > 0) {
            $('#selected-employees-info').show();
        } else {
            $('#selected-employees-info').hide();
        }
    },
    
    // التحقق من صحة الحدث
    validateEvent: function(employeeId, eventType, eventDate) {
        return $.ajax({
            url: '/events/api/validate',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                employee_id: employeeId,
                event_type: eventType,
                event_date: eventDate
            })
        });
    }
};

// وظائف التقارير
const ReportManager = {
    // تصدير البيانات
    exportData: function(format, reportType, filters = {}) {
        const params = new URLSearchParams(filters);
        params.append('format', format);
        
        const url = `/reports/export/${reportType}?${params.toString()}`;
        window.open(url, '_blank');
    },
    
    // تحديث الرسم البياني
    updateChart: function(chartId, apiUrl, chartType = 'bar') {
        const canvas = document.getElementById(chartId);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // إظهار مؤشر التحميل
        $(canvas).parent().append('<div class="loading-overlay"><i class="fas fa-spinner fa-spin fa-2x"></i></div>');
        
        $.get(apiUrl)
            .done(function(data) {
                // إزالة الرسم البياني السابق إن وجد
                if (window.charts && window.charts[chartId]) {
                    window.charts[chartId].destroy();
                }
                
                // إنشاء الرسم البياني الجديد
                const chart = new Chart(ctx, {
                    type: chartType,
                    data: data,
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: chartType === 'pie' || chartType === 'doughnut' ? 'bottom' : 'top'
                            }
                        },
                        scales: chartType === 'pie' || chartType === 'doughnut' ? {} : {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
                
                // حفظ مرجع الرسم البياني
                if (!window.charts) window.charts = {};
                window.charts[chartId] = chart;
            })
            .fail(function() {
                $(canvas).parent().html('<p class="text-center text-muted">خطأ في تحميل البيانات</p>');
            })
            .always(function() {
                $('.loading-overlay').remove();
            });
    }
};

// وظائف الموظفين
const EmployeeManager = {
    // تحديث صورة الموظف
    updatePhoto: function(employeeId, photoFile) {
        const formData = new FormData();
        formData.append('photo', photoFile);
        
        return $.ajax({
            url: `/employees/${employeeId}/photo`,
            method: 'POST',
            data: formData,
            processData: false,
            contentType: false
        });
    },
    
    // حساب الخدمة الفعلية
    calculateActualService: function(startDate, leaveEvents = []) {
        const start = moment(startDate);
        const now = moment();
        let totalDays = now.diff(start, 'days');
        
        // طرح أيام الإجازات
        leaveEvents.forEach(function(leave) {
            const leaveStart = moment(leave.start_date);
            const leaveEnd = moment(leave.end_date);
            const leaveDays = leaveEnd.diff(leaveStart, 'days');
            totalDays -= leaveDays;
        });
        
        const years = Math.floor(totalDays / 365);
        const months = Math.floor((totalDays % 365) / 30);
        const days = totalDays % 30;
        
        return {
            years: years,
            months: months,
            days: days,
            formatted: `${years} سنة، ${months} شهر، ${days} يوم`
        };
    }
};

// وظائف مساعدة
const Utils = {
    // تنسيق التاريخ
    formatDate: function(date, format = 'DD/MM/YYYY') {
        return moment(date).format(format);
    },
    
    // تنسيق الأرقام
    formatNumber: function(number) {
        return new Intl.NumberFormat('ar-EG').format(number);
    },
    
    // إظهار رسالة تأكيد
    confirmAction: function(message, callback) {
        if (confirm(message)) {
            callback();
        }
    },
    
    // إظهار رسالة نجاح
    showSuccess: function(message) {
        this.showAlert(message, 'success');
    },
    
    // إظهار رسالة خطأ
    showError: function(message) {
        this.showAlert(message, 'danger');
    },
    
    // إظهار تنبيه
    showAlert: function(message, type = 'info') {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show animate__animated animate__fadeInDown" role="alert">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        $('.main-content').prepend(alertHtml);
        
        // إزالة التنبيه تلقائياً بعد 5 ثوان
        setTimeout(function() {
            $('.alert').fadeOut();
        }, 5000);
    },
    
    // تحميل البيانات مع مؤشر التحميل
    loadWithSpinner: function(url, targetElement, callback) {
        $(targetElement).html('<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i></div>');
        
        $.get(url)
            .done(function(data) {
                if (callback) {
                    callback(data);
                } else {
                    $(targetElement).html(data);
                }
            })
            .fail(function() {
                $(targetElement).html('<p class="text-center text-muted">خطأ في تحميل البيانات</p>');
            });
    }
};

// معالجات الأحداث العامة
$(document).on('change', '#event-type-select', function() {
    EventManager.onEventTypeChange($(this).val());
});

$(document).on('change', '#select-all-employees', function() {
    EventManager.toggleAllEmployees($(this).is(':checked'));
});

$(document).on('change', '.category-select-all', function() {
    const category = $(this).data('category');
    EventManager.toggleCategoryEmployees(category, $(this).is(':checked'));
});

$(document).on('change', '.employee-checkbox', function() {
    EventManager.updateSelectedCount();
});

// تأكيد الحذف
$(document).on('click', '.delete-btn', function(e) {
    e.preventDefault();
    const form = $(this).closest('form');
    const itemName = $(this).data('item-name') || 'هذا العنصر';
    
    Utils.confirmAction(`هل أنت متأكد من حذف ${itemName}؟`, function() {
        form.submit();
    });
});

// تحديث الفلاتر
$(document).on('change', '.filter-select', function() {
    const form = $(this).closest('form');
    if (form.length) {
        form.submit();
    }
});

// إعادة تعيين الفلاتر
$(document).on('click', '.reset-filters', function() {
    const form = $(this).closest('form');
    form.find('input, select').val('');
    form.submit();
});

// تصدير البيانات
$(document).on('click', '.export-btn', function() {
    const format = $(this).data('format');
    const reportType = $(this).data('report-type');
    const filters = {};
    
    // جمع الفلاتر الحالية
    $('.filter-input, .filter-select').each(function() {
        const name = $(this).attr('name');
        const value = $(this).val();
        if (name && value) {
            filters[name] = value;
        }
    });
    
    ReportManager.exportData(format, reportType, filters);
});

// تحديث الرسوم البيانية
$(document).on('click', '.refresh-chart', function() {
    const chartId = $(this).data('chart-id');
    const apiUrl = $(this).data('api-url');
    const chartType = $(this).data('chart-type') || 'bar';
    
    ReportManager.updateChart(chartId, apiUrl, chartType);
});

// طباعة الصفحة
$(document).on('click', '.print-btn', function() {
    window.print();
});

// نسخ الرابط
$(document).on('click', '.copy-link', function() {
    const url = window.location.href;
    navigator.clipboard.writeText(url).then(function() {
        Utils.showSuccess('تم نسخ الرابط بنجاح');
    });
});

// تحديث الصفحة
$(document).on('click', '.refresh-page', function() {
    location.reload();
});

// إظهار/إخفاء كلمة المرور
$(document).on('click', '.toggle-password', function() {
    const input = $($(this).data('target'));
    const icon = $(this).find('i');
    
    if (input.attr('type') === 'password') {
        input.attr('type', 'text');
        icon.removeClass('fa-eye').addClass('fa-eye-slash');
    } else {
        input.attr('type', 'password');
        icon.removeClass('fa-eye-slash').addClass('fa-eye');
    }
});

// تحديد الكل في الجداول
$(document).on('change', '.select-all-table', function() {
    const table = $(this).closest('table');
    const checkboxes = table.find('tbody input[type="checkbox"]');
    checkboxes.prop('checked', $(this).is(':checked'));
});

// عمليات مجمعة
$(document).on('click', '.bulk-action-btn', function() {
    const action = $(this).data('action');
    const selectedItems = $('.table tbody input[type="checkbox"]:checked');
    
    if (selectedItems.length === 0) {
        Utils.showError('يرجى تحديد عنصر واحد على الأقل');
        return;
    }
    
    const ids = selectedItems.map(function() {
        return $(this).val();
    }).get();
    
    Utils.confirmAction(`هل أنت متأكد من تنفيذ هذا الإجراء على ${ids.length} عنصر؟`, function() {
        // تنفيذ العملية المجمعة
        performBulkAction(action, ids);
    });
});

// تنفيذ العملية المجمعة
function performBulkAction(action, ids) {
    $.ajax({
        url: '/api/bulk-action',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            action: action,
            ids: ids
        }),
        success: function(response) {
            Utils.showSuccess('تم تنفيذ العملية بنجاح');
            location.reload();
        },
        error: function() {
            Utils.showError('حدث خطأ أثناء تنفيذ العملية');
        }
    });
}

