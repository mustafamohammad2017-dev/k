using Microsoft.EntityFrameworkCore;
using EmployeePromotionSystem.Models;

namespace EmployeePromotionSystem.Data
{
    /// <summary>
    /// سياق قاعدة البيانات الرئيسي
    /// </summary>
    public class ApplicationDbContext : DbContext
    {
        public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options) : base(options)
        {
        }

        // الجداول
        public DbSet<Employee> Employees { get; set; }
        public DbSet<ProfessionalEvent> ProfessionalEvents { get; set; }
        public DbSet<PromotionHistory> PromotionHistories { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            // تكوين جدول الموظفين
            modelBuilder.Entity<Employee>(entity =>
            {
                entity.HasKey(e => e.Id);
                entity.Property(e => e.FullName).IsRequired().HasMaxLength(200);
                entity.Property(e => e.Title).HasMaxLength(100);
                entity.Property(e => e.AllowanceTracker).IsRequired().HasMaxLength(10);
                entity.Property(e => e.AcademicDegree).HasMaxLength(200);
                entity.Property(e => e.JobCategory).IsRequired().HasMaxLength(100);
                entity.Property(e => e.PhotoPath).HasMaxLength(500);

                // فهارس للبحث السريع
                entity.HasIndex(e => e.FullName);
                entity.HasIndex(e => e.JobCategory);
                entity.HasIndex(e => e.StartDate);
                entity.HasIndex(e => e.JobGrade);
            });

            // تكوين جدول الأحداث المهنية
            modelBuilder.Entity<ProfessionalEvent>(entity =>
            {
                entity.HasKey(e => e.Id);
                entity.Property(e => e.OfficialDocumentNumber).HasMaxLength(100);
                entity.Property(e => e.Notes).HasMaxLength(1000);
                entity.Property(e => e.NewJobCategory).HasMaxLength(100);
                entity.Property(e => e.NewAcademicDegree).HasMaxLength(200);

                // العلاقة مع الموظف
                entity.HasOne(e => e.Employee)
                      .WithMany(emp => emp.ProfessionalEvents)
                      .HasForeignKey(e => e.EmployeeId)
                      .OnDelete(DeleteBehavior.Cascade);

                // فهارس
                entity.HasIndex(e => e.EmployeeId);
                entity.HasIndex(e => e.EventDate);
                entity.HasIndex(e => e.EventType);
            });

            // تكوين جدول تاريخ الترفيعات
            modelBuilder.Entity<PromotionHistory>(entity =>
            {
                entity.HasKey(e => e.Id);
                entity.Property(e => e.Description).HasMaxLength(500);
                entity.Property(e => e.PreviousTracker).HasMaxLength(10);
                entity.Property(e => e.NewTracker).HasMaxLength(10);

                // العلاقة مع الموظف
                entity.HasOne(e => e.Employee)
                      .WithMany(emp => emp.PromotionHistory)
                      .HasForeignKey(e => e.EmployeeId)
                      .OnDelete(DeleteBehavior.Cascade);

                // فهارس
                entity.HasIndex(e => e.EmployeeId);
                entity.HasIndex(e => e.EventDate);
                entity.HasIndex(e => e.PromotionType);
            });

            // بيانات أولية للاختبار
            SeedData(modelBuilder);
        }

        /// <summary>
        /// إضافة بيانات أولية للاختبار
        /// </summary>
        private void SeedData(ModelBuilder modelBuilder)
        {
            // موظفين للاختبار
            modelBuilder.Entity<Employee>().HasData(
                new Employee
                {
                    Id = 1,
                    FullName = "أحمد محمد علي حسن",
                    Title = "مدرس",
                    StartDate = new DateTime(2020, 1, 15),
                    LastAllowanceDate = new DateTime(2023, 1, 15),
                    LastPromotionDate = new DateTime(2020, 1, 15),
                    AllowanceTracker = "2/4",
                    AcademicDegree = "ماجستير",
                    JobCategory = "تدريسي",
                    JobTitle = 101,
                    JobGrade = 7,
                    JobStage = 3,
                    CreatedAt = DateTime.Now,
                    UpdatedAt = DateTime.Now
                },
                new Employee
                {
                    Id = 2,
                    FullName = "فاطمة عبد الله محمود",
                    Title = "مدرس مساعد",
                    StartDate = new DateTime(2021, 9, 1),
                    LastAllowanceDate = new DateTime(2023, 9, 1),
                    LastPromotionDate = new DateTime(2021, 9, 1),
                    AllowanceTracker = "1/4",
                    AcademicDegree = "بكالوريوس",
                    JobCategory = "تدريسي",
                    JobTitle = 102,
                    JobGrade = 8,
                    JobStage = 2,
                    CreatedAt = DateTime.Now,
                    UpdatedAt = DateTime.Now
                },
                new Employee
                {
                    Id = 3,
                    FullName = "محمد عبد الرحمن صالح",
                    Title = "موظف إداري",
                    StartDate = new DateTime(2019, 3, 10),
                    LastAllowanceDate = new DateTime(2023, 3, 10),
                    LastPromotionDate = new DateTime(2022, 3, 10),
                    AllowanceTracker = "0/5",
                    AcademicDegree = "دبلوم",
                    JobCategory = "إداري",
                    JobTitle = 201,
                    JobGrade = 5,
                    JobStage = 1,
                    CreatedAt = DateTime.Now,
                    UpdatedAt = DateTime.Now
                }
            );
        }
    }
}

