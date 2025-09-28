using Microsoft.EntityFrameworkCore;
using EmployeePromotionSystem.Data;
using EmployeePromotionSystem.Models;

namespace EmployeePromotionSystem.Services
{
    /// <summary>
    /// خدمة إدارة الموظفين
    /// </summary>
    public class EmployeeService : IEmployeeService
    {
        private readonly ApplicationDbContext _context;
        private readonly ICalculationEngine _calculationEngine;
        private readonly ILogger<EmployeeService> _logger;

        public EmployeeService(
            ApplicationDbContext context, 
            ICalculationEngine calculationEngine,
            ILogger<EmployeeService> logger)
        {
            _context = context;
            _calculationEngine = calculationEngine;
            _logger = logger;
        }

        /// <summary>
        /// الحصول على جميع الموظفين
        /// </summary>
        public async Task<List<Employee>> GetAllEmployeesAsync()
        {
            return await _context.Employees
                .Include(e => e.ProfessionalEvents)
                .Include(e => e.PromotionHistory)
                .OrderBy(e => e.FullName)
                .ToListAsync();
        }

        /// <summary>
        /// الحصول على موظف بالمعرف
        /// </summary>
        public async Task<Employee?> GetEmployeeByIdAsync(int id)
        {
            var employee = await _context.Employees
                .Include(e => e.ProfessionalEvents.OrderBy(pe => pe.EventDate))
                .Include(e => e.PromotionHistory.OrderBy(ph => ph.EventDate))
                .FirstOrDefaultAsync(e => e.Id == id);

            if (employee != null)
            {
                // تحديث الاستحقاقات تلقائياً عند عرض ملف الموظف
                await _calculationEngine.CalculateAndApplyEntitlementsAsync(employee);
            }

            return employee;
        }

        /// <summary>
        /// إضافة موظف جديد
        /// </summary>
        public async Task<Employee> AddEmployeeAsync(Employee employee)
        {
            // التحقق من صحة البيانات
            ValidateEmployee(employee);

            employee.CreatedAt = DateTime.Now;
            employee.UpdatedAt = DateTime.Now;

            _context.Employees.Add(employee);
            await _context.SaveChangesAsync();

            _logger.LogInformation($"تم إضافة موظف جديد: {employee.FullName}");

            // حساب الاستحقاقات الأولية
            await _calculationEngine.CalculateAndApplyEntitlementsAsync(employee);

            return employee;
        }

        /// <summary>
        /// تحديث بيانات موظف
        /// </summary>
        public async Task<Employee> UpdateEmployeeAsync(Employee employee)
        {
            var existingEmployee = await _context.Employees.FindAsync(employee.Id);
            if (existingEmployee == null)
            {
                throw new ArgumentException("الموظف غير موجود");
            }

            // التحقق من صحة البيانات
            ValidateEmployee(employee);

            // تحديث البيانات
            existingEmployee.FullName = employee.FullName;
            existingEmployee.Title = employee.Title;
            existingEmployee.AcademicDegree = employee.AcademicDegree;
            existingEmployee.JobCategory = employee.JobCategory;
            existingEmployee.JobTitle = employee.JobTitle;
            existingEmployee.UpdatedAt = DateTime.Now;

            await _context.SaveChangesAsync();

            _logger.LogInformation($"تم تحديث بيانات الموظف: {employee.FullName}");

            return existingEmployee;
        }

        /// <summary>
        /// حذف موظف
        /// </summary>
        public async Task<bool> DeleteEmployeeAsync(int id)
        {
            var employee = await _context.Employees.FindAsync(id);
            if (employee == null)
            {
                return false;
            }

            _context.Employees.Remove(employee);
            await _context.SaveChangesAsync();

            _logger.LogInformation($"تم حذف الموظف: {employee.FullName}");

            return true;
        }

        /// <summary>
        /// البحث في الموظفين
        /// </summary>
        public async Task<List<Employee>> SearchEmployeesAsync(string searchTerm)
        {
            if (string.IsNullOrWhiteSpace(searchTerm))
            {
                return await GetAllEmployeesAsync();
            }

            searchTerm = searchTerm.Trim().ToLower();

            return await _context.Employees
                .Include(e => e.ProfessionalEvents)
                .Include(e => e.PromotionHistory)
                .Where(e => e.FullName.ToLower().Contains(searchTerm) ||
                           e.JobCategory.ToLower().Contains(searchTerm) ||
                           e.AcademicDegree.ToLower().Contains(searchTerm))
                .OrderBy(e => e.FullName)
                .ToListAsync();
        }

        /// <summary>
        /// فلترة الموظفين حسب الصنف الوظيفي
        /// </summary>
        public async Task<List<Employee>> GetEmployeesByJobCategoryAsync(string jobCategory)
        {
            return await _context.Employees
                .Include(e => e.ProfessionalEvents)
                .Include(e => e.PromotionHistory)
                .Where(e => e.JobCategory == jobCategory)
                .OrderBy(e => e.FullName)
                .ToListAsync();
        }

        /// <summary>
        /// فلترة الموظفين حسب الدرجة الوظيفية
        /// </summary>
        public async Task<List<Employee>> GetEmployeesByGradeAsync(int grade)
        {
            return await _context.Employees
                .Include(e => e.ProfessionalEvents)
                .Include(e => e.PromotionHistory)
                .Where(e => e.JobGrade == grade)
                .OrderBy(e => e.FullName)
                .ToListAsync();
        }

        /// <summary>
        /// الحصول على الموظفين مع تفاصيل الاستحقاق القادم
        /// </summary>
        public async Task<List<EmployeeWithNextEntitlement>> GetEmployeesWithNextEntitlementAsync()
        {
            var employees = await GetAllEmployeesAsync();
            var result = new List<EmployeeWithNextEntitlement>();

            foreach (var employee in employees)
            {
                var nextDate = await _calculationEngine.CalculateNextEntitlementDateAsync(employee);
                var nextType = _calculationEngine.GetNextEntitlementType(employee);
                var (nextGrade, nextStage) = _calculationEngine.CalculateNextGradeStage(employee);

                result.Add(new EmployeeWithNextEntitlement
                {
                    Employee = employee,
                    NextEntitlementDate = nextDate,
                    NextEntitlementType = nextType,
                    NextGradeStage = $"الدرجة {nextGrade} - المرحلة {nextStage}",
                    DaysUntilEntitlement = (int)(nextDate - DateTime.Now).TotalDays
                });
            }

            return result.OrderBy(e => e.NextEntitlementDate).ToList();
        }

        /// <summary>
        /// الحصول على إحصائيات الموظفين
        /// </summary>
        public async Task<EmployeeStatistics> GetEmployeeStatisticsAsync()
        {
            var employees = await GetAllEmployeesAsync();
            var employeesWithEntitlements = await GetEmployeesWithNextEntitlementAsync();

            var statistics = new EmployeeStatistics
            {
                TotalEmployees = employees.Count,
                TeachingStaff = employees.Count(e => e.JobCategory.Contains("تدريسي")),
                AdministrativeStaff = employees.Count(e => e.JobCategory.Contains("إداري")),
                EmployeesByGrade = employees.GroupBy(e => e.JobGrade)
                    .ToDictionary(g => g.Key, g => g.Count()),
                EmployeesByCategory = employees.GroupBy(e => e.JobCategory)
                    .ToDictionary(g => g.Key, g => g.Count()),
                EmployeesEligibleForPromotion = employeesWithEntitlements
                    .Count(e => e.NextEntitlementType == PromotionType.Promotion && e.DaysUntilEntitlement <= 0),
                EmployeesEligibleForAllowance = employeesWithEntitlements
                    .Count(e => e.NextEntitlementType == PromotionType.Allowance && e.DaysUntilEntitlement <= 0)
            };

            return statistics;
        }

        /// <summary>
        /// تحديث صورة الموظف
        /// </summary>
        public async Task<bool> UpdateEmployeePhotoAsync(int employeeId, string photoPath)
        {
            var employee = await _context.Employees.FindAsync(employeeId);
            if (employee == null)
            {
                return false;
            }

            employee.PhotoPath = photoPath;
            employee.UpdatedAt = DateTime.Now;

            await _context.SaveChangesAsync();
            return true;
        }

        /// <summary>
        /// الحصول على الأصناف الوظيفية المتاحة
        /// </summary>
        public async Task<List<string>> GetJobCategoriesAsync()
        {
            return await _context.Employees
                .Select(e => e.JobCategory)
                .Distinct()
                .OrderBy(c => c)
                .ToListAsync();
        }

        /// <summary>
        /// التحقق من صحة بيانات الموظف
        /// </summary>
        private void ValidateEmployee(Employee employee)
        {
            if (string.IsNullOrWhiteSpace(employee.FullName))
            {
                throw new ArgumentException("اسم الموظف مطلوب");
            }

            if (employee.StartDate > DateTime.Now)
            {
                throw new ArgumentException("تاريخ المباشرة لا يمكن أن يكون في المستقبل");
            }

            if (employee.JobGrade < 1 || employee.JobGrade > 10)
            {
                throw new ArgumentException("الدرجة الوظيفية يجب أن تكون بين 1 و 10");
            }

            if (employee.JobStage < 1 || employee.JobStage > 11)
            {
                throw new ArgumentException("المرحلة الوظيفية يجب أن تكون بين 1 و 11");
            }

            if (!_calculationEngine.ValidateTracker(employee.AllowanceTracker, employee.JobGrade))
            {
                throw new ArgumentException("مؤشر تتبع العلاوة غير صحيح");
            }
        }
    }
}

