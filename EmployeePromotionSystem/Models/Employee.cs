using System.ComponentModel.DataAnnotations;

namespace EmployeePromotionSystem.Models
{
    /// <summary>
    /// نموذج بيانات الموظف
    /// </summary>
    public class Employee
    {
        [Key]
        public int Id { get; set; }

        [Required(ErrorMessage = "الاسم الرباعي مطلوب")]
        [StringLength(200, ErrorMessage = "الاسم لا يجب أن يتجاوز 200 حرف")]
        public string FullName { get; set; } = string.Empty;

        [StringLength(100, ErrorMessage = "اللقب لا يجب أن يتجاوز 100 حرف")]
        public string Title { get; set; } = string.Empty;

        [Required(ErrorMessage = "تاريخ المباشرة مطلوب")]
        public DateTime StartDate { get; set; }

        [Required(ErrorMessage = "تاريخ آخر استحقاق للعلاوة مطلوب")]
        public DateTime LastAllowanceDate { get; set; }

        [Required(ErrorMessage = "تاريخ آخر استحقاق للترفيع مطلوب")]
        public DateTime LastPromotionDate { get; set; }

        [Required(ErrorMessage = "مؤشر تتبع العلاوة مطلوب")]
        [StringLength(10)]
        public string AllowanceTracker { get; set; } = "0/4"; // مثل 4/0, 4/1, 4/2, 4/3, 5/0, 5/1, 5/2, 5/3, 5/4

        [StringLength(200, ErrorMessage = "الشهادة العلمية لا يجب أن تتجاوز 200 حرف")]
        public string AcademicDegree { get; set; } = string.Empty;

        [Required(ErrorMessage = "صنف الوظيفة مطلوب")]
        [StringLength(100, ErrorMessage = "صنف الوظيفة لا يجب أن يتجاوز 100 حرف")]
        public string JobCategory { get; set; } = string.Empty;

        [Required(ErrorMessage = "العنوان الوظيفي مطلوب")]
        public int JobTitle { get; set; }

        [Required(ErrorMessage = "الدرجة الوظيفية مطلوبة")]
        [Range(1, 10, ErrorMessage = "الدرجة الوظيفية يجب أن تكون بين 1 و 10")]
        public int JobGrade { get; set; }

        [Required(ErrorMessage = "المرحلة الوظيفية مطلوبة")]
        [Range(1, 11, ErrorMessage = "المرحلة الوظيفية يجب أن تكون بين 1 و 11")]
        public int JobStage { get; set; } = 1;

        public string? PhotoPath { get; set; }

        public DateTime CreatedAt { get; set; } = DateTime.Now;
        public DateTime UpdatedAt { get; set; } = DateTime.Now;

        // العلاقات
        public virtual ICollection<ProfessionalEvent> ProfessionalEvents { get; set; } = new List<ProfessionalEvent>();
        public virtual ICollection<PromotionHistory> PromotionHistory { get; set; } = new List<PromotionHistory>();

        // خصائص محسوبة
        public TimeSpan ActualService => DateTime.Now - StartDate;
        public string ActualServiceFormatted => $"{ActualService.Days / 365} سنة، {(ActualService.Days % 365) / 30} شهر، {ActualService.Days % 30} يوم";

        public string CurrentGradeStage => $"الدرجة {JobGrade} - المرحلة {JobStage}";

        /// <summary>
        /// حساب نوع الاستحقاق القادم (علاوة أم ترفيع)
        /// </summary>
        public string NextEntitlementType
        {
            get
            {
                var parts = AllowanceTracker.Split('/');
                if (parts.Length != 2) return "غير محدد";

                if (int.TryParse(parts[0], out int current) && int.TryParse(parts[1], out int total))
                {
                    return current == total - 1 ? "ترفيع" : "علاوة";
                }
                return "غير محدد";
            }
        }

        /// <summary>
        /// حساب الدرجة والمرحلة القادمة
        /// </summary>
        public string NextGradeStage
        {
            get
            {
                if (NextEntitlementType == "علاوة")
                {
                    return $"الدرجة {JobGrade} - المرحلة {JobStage + 1}";
                }
                else if (NextEntitlementType == "ترفيع" && JobGrade > 1)
                {
                    return $"الدرجة {JobGrade - 1} - المرحلة 1";
                }
                return CurrentGradeStage;
            }
        }
    }
}

