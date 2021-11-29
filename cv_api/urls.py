from django.urls import path, include
from django.urls.conf import re_path
from django.views.generic import base
from rest_framework import routers
from . import views
# from  import LoginView

router = routers.DefaultRouter()
router.register(r'configuracioncv', views.ConfiguracionCvView)
router.register(r'configuracioncv_personalizado', views.ConfiguracionCv_PersonalizadoView)
router.register(r'usuario', views.UsarioView)
# router.register(r'administrador', views.AdministradorView)
router.register(r'bloque', views.BloqueView)
# router.register(r'vistapdf', views.data, basename='mymodel')


urlpatterns = [
  path('', include(router.urls)),
  path('login/', views.LoginView.as_view()),   
  path('pdf-completo/<int:id>', views.PdfCompleto),
  path('pdf-resumido/<int:id>', views.PdfResumido), 
  path('doc-completo/<int:id>', views.DocCompleto),
  path('doc-resumido/<int:id>', views.DocResumido),
  path('json-completo/<int:id>', views.JsonCompleto),
  path('json-resumido/<int:id>', views.JsonResumido),
  path('txt-informacion/<int:id>', views.GeneraTxtInformacion),
  path('informacion_txt_articulos/<int:id>', views.InformacionTxtArticulos),
  path('informacion_txt_libros/<int:id>', views.InformacionTxtLibros),
  path('informacion_txt_proyectos/<int:id>', views.InformacionTxtProyectos),
  path('informacion_txt_capacitaciones/<int:id>', views.InformacionTxtCapacitacion),  
  path('informacion_txt_gradoacademico/<int:id>', views.InformacionTxtGradoAcademico),
  path('informacion_csv/<int:id>', views.InformacionCsv),
  path('pdf-personalizado/<int:id>/<slug:nombre_cv>/<slug:cvHash>', views.PdfPersonalizado),
  path('doc-personalizado/<int:id>/<slug:nombre_cv>/<slug:cvHash>', views.DocPersonalizado),
  path('json-personalizado/<int:id>/<slug:nombre_cv>/<slug:cvHash>', views.JsonPersonalizado),
  path('elimina-personalizados/<slug:nombre_cv>/<slug:cv>', views.eliminaPersonalizados),
  path('personalizados/<int:id_user>/<slug:bloque>/<slug:nombre_cv>/<slug:cv>', views.getConfPersonalizada),
  path('crea-bibtext/<int:id>', views.generaBibTex),
  path('prueba/<int:id>', views.informacionCsvLibros),
  re_path('^personalizacion_usuario/(?P<id_user>.+)/$', views.PersonalizacionUsuario.as_view()),
]