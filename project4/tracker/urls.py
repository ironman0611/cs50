from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('register', views.register, name='register'),
    path('api/tasks/<int:application_id>', views.get_tasks, name='get_tasks'),
    path('api/task/<int:task_id>/toggle', views.toggle_task, name='toggle_task'),

]
