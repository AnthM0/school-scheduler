from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('schedule-template/', views.schedule_template, name='schedule_template'),
    path('schedule-template/create-class/', views.create_class, name='create_class'),
    path('schedule-template/edit-class/<int:class_id>/', views.edit_class, name='edit_class'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]