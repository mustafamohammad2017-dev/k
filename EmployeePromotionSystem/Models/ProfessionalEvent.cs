using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace EmployeePromotionSystem.Models
{
    /// <summary>
    /// نموذج الأحداث المهنية
    /// </summary>
    public class ProfessionalEvent
    {
        [Key]
        public int Id { get; set; }

        [Required]
        public int EmployeeId { get; set; }

        [Required(ErrorMessage = "نوع الحدث مطلوب")]
        public EventType EventType { get; set; }

        [Required(ErrorMessage = "تاريخ الحدث مطلوب")]
        public DateTime EventDate { get; set; }

        [StringLength(100, ErrorMessage = "رقم الكتاب الرسمي لا يجب أن يتجاوز 100 حرف")]
        public string? OfficialDocumentNumber { get; set; }

        public DateTime? OfficialDocumentDate { get; set; }

        [StringLength(1000, ErrorMessage = "الملاحظات لا يجب أن تتجاوز 1000 حرف")]
        public string? Notes { get; set; }

        // خصائص خاصة بكتب الشكر
        public int? ReductionMonths { get; set; } // عدد الأشهر المقللة (1-6)

        // خصائص خاصة بالإجازات
        public DateTime? LeaveStartDate { get; set; }
        public DateTime? LeaveEndDate { get; set; }

        // خصائص خاصة بالأحداث المخصصة
        public AdjustmentType? AdjustmentType { get; set; }
        public int? AdjustmentMonths { get; set; }

        // خصائص خاصة بالشهادات الجديدة
        [StringLength(100)]
        public string? NewJobCategory { get; set; }
        public int? NewJobTitle { get; set; }
        [StringLength(200)]
        public string? NewAcademicDegree { get; set; }

        public DateTime CreatedAt { get; set; } = DateTime.Now;

        // العلاقات
        [ForeignKey("EmployeeId")]
        public virtual Employee Employee { get; set; } = null!;

        /// <summary>
        /// حساب تأثير الحدث على مدة الاستحقاق بالأشهر
        /// </summary>
        public int GetImpactInMonths()
        {
            return EventType switch
            {
                EventType.CommendationLetter => -(ReductionMonths ?? 0),
                EventType.HigherDegree => -12, // Step واحد = 12 شهر
                EventType.NoticePenalty => 3,
                EventType.WarningPenalty => 6,
                EventType.ReprimandPenalty => 12,
                EventType.UnpaidLeave or EventType.DisabilityLeave or EventType.FiveYearLeave or EventType.MaternityLeave => 
                    LeaveStartDate.HasValue && LeaveEndDate.HasValue 
                        ? (int)(LeaveEndDate.Value - LeaveStartDate.Value).TotalDays / 30 
                        : 0,
                EventType.CustomEvent => AdjustmentType == Models.AdjustmentType.Add 
                    ? (AdjustmentMonths ?? 0) 
                    : -(AdjustmentMonths ?? 0),
                _ => 0
            };
        }

        /// <summary>
        /// وصف تأثير الحدث
        /// </summary>
        public string ImpactDescription
        {
            get
            {
                var impact = GetImpactInMonths();
                return impact switch
                {
                    > 0 => $"إضافة {impact} شهر للاستحقاق القادم",
                    < 0 => $"تقليل {Math.Abs(impact)} شهر من الاستحقاق القادم",
                    _ => "لا يوجد تأثير على الاستحقاق"
                };
            }
        }
    }

    /// <summary>
    /// أنواع الأحداث المهنية
    /// </summary>
    public enum EventType
    {
        [Display(Name = "كتاب شكر وتقدير")]
        CommendationLetter = 1,

        [Display(Name = "الحصول على شهادة أعلى")]
        HigherDegree = 2,

        [Display(Name = "عقوبة لفت نظر")]
        NoticePenalty = 3,

        [Display(Name = "عقوبة إنذار")]
        WarningPenalty = 4,

        [Display(Name = "عقوبة توبيخ")]
        ReprimandPenalty = 5,

        [Display(Name = "إجازة بدون راتب")]
        UnpaidLeave = 6,

        [Display(Name = "إجازة رعاية المعاقين")]
        DisabilityLeave = 7,

        [Display(Name = "إجازة الخمس سنوات")]
        FiveYearLeave = 8,

        [Display(Name = "إجازة أمومة")]
        MaternityLeave = 9,

        [Display(Name = "حدث مخصص")]
        CustomEvent = 10
    }

    /// <summary>
    /// نوع التعديل للأحداث المخصصة
    /// </summary>
    public enum AdjustmentType
    {
        [Display(Name = "إضافة مدة")]
        Add = 1,

        [Display(Name = "طرح مدة")]
        Subtract = 2
    }
}

