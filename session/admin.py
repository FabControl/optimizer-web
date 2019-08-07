from django.contrib import admin

# Register your models here.
from .models import *


admin.site.register(Material)
admin.site.register(Machine)
admin.site.register(Session)
admin.site.register(Nozzle)
admin.site.register(Extruder)
admin.site.register(Chamber)
admin.site.register(Printbed)
admin.site.register(Settings)
