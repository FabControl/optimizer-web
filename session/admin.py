from django.contrib import admin

# Register your models here.
from .models import Material, Machine, Session


admin.site.register(Material)
admin.site.register(Machine)
admin.site.register(Session)
