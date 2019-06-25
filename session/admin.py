from django.contrib import admin

# Register your models here.
from .models import Material, Machine


admin.site.register(Material)
admin.site.register(Machine)