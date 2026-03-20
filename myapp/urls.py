from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('schedule-template/', views.schedule_template, name='schedule_template'),
    path('schedule-template/create-class/', views.create_class, name='create_class'),
    path('schedule-template/edit-class/<int:class_id>/', views.edit_class, name='edit_class'),
    path('schedule-template/delete-class/<int:class_id>/', views.delete_class, name='delete_class'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('users-and-permissions/', views.users_and_permissions, name='users_and_permissions'),
    path('users-and-permissions/edit-user/<int:user_id>/', views.edit_user, name='edit_user'),
    path('users-and-permissions/delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('users-and-permissions/edit-group/<int:group_id>/', views.edit_group, name='edit_group'),
    path('users-and-permissions/delete-group/<int:group_id>/', views.delete_group, name='delete_group'),
]