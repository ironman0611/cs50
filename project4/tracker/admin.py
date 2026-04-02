from django.contrib import admin
from .models import College, Application, Task

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
