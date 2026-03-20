# This file makes the views/ folder a Python package and exposes
# all views so that myapp/urls.py can continue importing from
# .views without any changes.

from .home_views import home
from .auth_views import login_view, register_view, logout_view
from .schedule_views import schedule_template, create_class, edit_class, delete_class
from .admin_views import users_and_permissions, edit_user, delete_user, edit_group, delete_group