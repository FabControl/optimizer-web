from django.contrib import admin

# Register your models here.
from .models import *


admin.site.register(SessionMode)
admin.site.register(Junction)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'pub_date', 'owner', 'material', 'mode', 'completed_tests')
    search_fields = ('name', 'owner__email', 'material__name', 'machine__model')
    sortable_by = ('name', 'pub_date', 'owner', 'material', 'completed_tests')
    date_hierarchy = 'pub_date'


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ('model', 'pub_date', 'owner', 'form')
    search_fields = ('name', 'owner__email', 'form')
    sortable_by = ('model', 'pub_date', 'owner', 'form')
    date_hierarchy = 'pub_date'


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'pub_date', 'owner', 'size_od')
    search_fields = ('name', 'owner__email', 'size_od')
    sortable_by = ('name', 'pub_date', 'owner', 'size_od')
    date_hierarchy = 'pub_date'


@admin.register(PrintDescriptor)
class PrintDescriptorAdmin(admin.ModelAdmin):
    list_display = ('statement', 'target_test', 'hint')