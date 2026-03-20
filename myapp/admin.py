from django.contrib import admin
from .models import Class, Group, UserProfile

admin.site.register(Class)
admin.site.register(Group)
admin.site.register(UserProfile)