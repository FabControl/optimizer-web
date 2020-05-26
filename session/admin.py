from django.contrib import admin

# Register your models here.
from .models import *


admin.site.register(Material)
admin.site.register(Machine)
admin.site.register(SessionMode)
admin.site.register(PrintDescriptor)
admin.site.register(Junction)


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'pub_date', 'owner', 'material', 'mode', 'completed_tests')
    search_fields = ('name', 'owner__email', 'material__name')
    sortable_by = ('name', 'pub_date', 'owner', 'material', 'completed_tests')
    date_hierarchy = 'pub_date'

