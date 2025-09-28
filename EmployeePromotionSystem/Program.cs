using EmployeePromotionSystem.Components;
using EmployeePromotionSystem.Data;
using EmployeePromotionSystem.Services;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

// إضافة قاعدة البيانات
builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseSqlite(builder.Configuration.GetConnectionString("DefaultConnection") ?? 
                     "Data Source=EmployeePromotion.db"));

// إضافة الخدمات المخصصة
builder.Services.AddScoped<ICalculationEngine, CalculationEngine>();
builder.Services.AddScoped<IEmployeeService, EmployeeService>();

// إضافة خدمات إضافية
builder.Services.AddLogging();

var app = builder.Build();

// إنشاء قاعدة البيانات تلقائياً
using (var scope = app.Services.CreateScope())
{
    var context = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
    context.Database.EnsureCreated();
}

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error", createScopeForErrors: true);
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}

app.UseHttpsRedirection();

app.UseStaticFiles();
app.UseAntiforgery();

app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();

