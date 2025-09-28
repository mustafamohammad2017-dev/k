using EmployeePromotionSystem.Models;

namespace EmployeePromotionSystem.Services
{
    /// <summary>
    /// واجهة خدمة إدارة الموظفين
    /// </summary>
    public interface IEmployeeService
    {
        /// <summary>
        /// الحصول على جميع الموظفين
        /// </summary>
        Task<List<Employee>> GetAllEmployeesAsync();

        /// <summary>
        /// الحصول على موظف بالمعرف
        /// </summary>
        Task<Employee?> GetEmployeeByIdAsync(int id);

        /// <summary>
        /// إضافة موظف جديد
        /// </summary>
        Task<Employee> AddEmployeeAsync(Employee employee);

        /// <summary>
        /// تحديث بيانات موظف
        /// </summary>
        Task<Employee> UpdateEmployeeAsync(Employee employee);

        /// <summary>
        /// حذف موظف
        /// </summary>
        Task<bool> DeleteEmployeeAsync(int id);

        /// <summary>
        /// البحث في الموظفين
        /// </summary>
        Task<List<Employee>> SearchEmployeesAsync(string searchTerm);

        /// <summary>
        /// فلترة الموظفين حسب الصنف الوظيفي
        /// </summary>
        Task<List<Employee>> GetEmployeesByJobCategoryAsync(string jobCategory);

        /// <summary>
        /// فلترة الموظفين حسب الدرجة الوظيفية
        /// </summary>
        Task<List<Employee>> GetEmployeesByGradeAsync(int grade);

        /// <summary>
        /// الحصول على الموظفين مع تفاصيل الاستحقاق القادم
        /// </summary>
        Task<List<EmployeeWithNextEntitlement>> GetEmployeesWithNextEntitlementAsync();

        /// <summary>
        /// الحصول على إحصائيات الموظفين
        /// </summary>
        Task<EmployeeStatistics> GetEmployeeStatisticsAsync();

        /// <summary>
        /// تحديث صورة الموظف
        /// </summary>
        Task<bool> UpdateEmployeePhotoAsync(int employeeId, string photoPath);

        /// <summary>
        /// الحصول على الأصناف الوظيفية المتاحة
        /// </summary>
        Task<List<string>> GetJobCategoriesAsync();
    }

    /// <summary>
    /// نموذج الموظف مع تفاصيل الاستحقاق القادم
    /// </summary>
    public class EmployeeWithNextEntitlement
    {
        public Employee Employee { get; set; } = null!;
        public DateTime NextEntitlementDate { get; set; }
        public PromotionType NextEntitlementType { get; set; }
        public string NextGradeStage { get; set; } = string.Empty;
        public int DaysUntilEntitlement { get; set; }
    }

    /// <summary>
    /// إحصائيات الموظفين
    /// </summary>
    public class EmployeeStatistics
    {
        public int TotalEmployees { get; set; }
        public int TeachingStaff { get; set; }
        public int AdministrativeStaff { get; set; }
        public Dictionary<int, int> EmployeesByGrade { get; set; } = new();
        public Dictionary<string, int> EmployeesByCategory { get; set; } = new();
        public int EmployeesEligibleForPromotion { get; set; }
        public int EmployeesEligibleForAllowance { get; set; }
    }
}

