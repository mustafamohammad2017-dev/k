using EmployeePromotionSystem.Models;

namespace EmployeePromotionSystem.Services
{
    /// <summary>
    /// واجهة المحرك الذكي للحسابات
    /// </summary>
    public interface ICalculationEngine
    {
        /// <summary>
        /// حساب وتطبيق جميع العلاوات والترفيعات المستحقة للموظف
        /// </summary>
        /// <param name="employee">الموظف</param>
        /// <returns>قائمة بالأحداث الجديدة التي تم تطبيقها</returns>
        Task<List<PromotionHistory>> CalculateAndApplyEntitlementsAsync(Employee employee);

        /// <summary>
        /// حساب تاريخ الاستحقاق القادم للموظف
        /// </summary>
        /// <param name="employee">الموظف</param>
        /// <returns>تاريخ الاستحقاق القادم</returns>
        Task<DateTime> CalculateNextEntitlementDateAsync(Employee employee);

        /// <summary>
        /// حساب نوع الاستحقاق القادم (علاوة أم ترفيع)
        /// </summary>
        /// <param name="employee">الموظف</param>
        /// <returns>نوع الاستحقاق</returns>
        PromotionType GetNextEntitlementType(Employee employee);

        /// <summary>
        /// حساب الدرجة والمرحلة القادمة
        /// </summary>
        /// <param name="employee">الموظف</param>
        /// <returns>الدرجة والمرحلة القادمة</returns>
        (int grade, int stage) CalculateNextGradeStage(Employee employee);

        /// <summary>
        /// حساب تأثير الأحداث المهنية على مدة الاستحقاق
        /// </summary>
        /// <param name="events">قائمة الأحداث المهنية</param>
        /// <param name="baseDate">التاريخ الأساسي للحساب</param>
        /// <returns>عدد الأشهر المضافة أو المطروحة</returns>
        int CalculateEventsImpact(IEnumerable<ProfessionalEvent> events, DateTime baseDate);

        /// <summary>
        /// التحقق من صحة مؤشر التتبع
        /// </summary>
        /// <param name="tracker">مؤشر التتبع</param>
        /// <param name="grade">الدرجة الوظيفية</param>
        /// <returns>true إذا كان صحيحاً</returns>
        bool ValidateTracker(string tracker, int grade);

        /// <summary>
        /// إعادة حساب كامل للموظف من نقطة البداية
        /// </summary>
        /// <param name="employee">الموظف</param>
        /// <returns>قائمة بجميع الأحداث المحسوبة</returns>
        Task<List<PromotionHistory>> RecalculateFromStartAsync(Employee employee);
    }
}

