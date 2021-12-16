from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Register your models here.
from . models import *

admin.site.register(ConfiguracionCv)
# admin.site.register(Administrador)
admin.site.register(Usuario, UserAdmin)
admin.site.register(ConfiguracionCv_Personalizado)
# admin.site.register(Servicio)

# admin.site.register(ConfiguracionCv_Personalizado)
