from django.contrib import admin
from .models import College, Application, Task

admin.site.site_header = "College Administration"
admin.site.site_title = "College Administration"
admin.site.index_title = "College Administration"

class TaskInline(admin.TabularInline):
    model = Task
    extra = 1

class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['user', 'college', 'status', 'created_at']
    list_filter = ['status']
    inlines = [TaskInline]

admin.site.register(College)
admin.site.register(Application, ApplicationAdmin)
admin.site.register(Task)
