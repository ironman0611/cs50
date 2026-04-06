from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('colleges', views.all_colleges, name='all_colleges'),
    path('my-colleges', views.my_colleges, name='my_colleges'),
    path('apply', views.apply_college, name='apply_college'),
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('register', views.register, name='register'),
    path('api/tasks/<int:application_id>', views.get_tasks, name='get_tasks'),
    path('api/task/<int:task_id>/toggle', views.toggle_task, name='toggle_task'),

]
