from django.urls import path, include
from django.urls.conf import re_path
from django.views.generic import base
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'configuracioncv', views.ConfiguracionCvView)
router.register(r'configuracioncv_personalizado', views.ConfiguracionCv_PersonalizadoView)
router.register(r'usuario', views.UsarioView)
router.register(r'bloque', views.BloqueView)
router.register(r'servicio', views.ServicioView)


urlpatterns = [
  path('', include(router.urls)),
  path('login/', views.LoginView.as_view()),   
  path('pdf-completo/<int:id>', views.PdfCompleto),
  path('pdf-resumido/<int:id>', views.PdfResumido), 
  path('doc-completo/<int:id>', views.DocCompleto),
  path('doc-resumido/<int:id>', views.DocResumido),
  path('json-completo/<int:id>', views.JsonCompleto),
  path('json-resumido/<int:id>', views.JsonResumido),
  path('txt-informacion/<str:bloque>/<int:idDocente>', views.InformacionTxt),
  path('pdf-personalizado/<int:id>/<slug:nombre_cv>/<slug:cvHash>', views.PdfPersonalizado),
  path('doc-personalizado/<int:id>/<slug:nombre_cv>/<slug:cvHash>', views.DocPersonalizado),
  path('json-personalizado/<int:id>/<slug:nombre_cv>/<slug:cvHash>', views.JsonPersonalizado),
  path('elimina-personalizados/<slug:nombre_cv>/<slug:cv>', views.eliminaPersonalizados), 
  path('elimina-objeto/<str:bloque>/<slug:atributo>', views.eliminaObjetoConfiguracion), 
  path('elimina-objetobloque/<slug:bloque>', views.eliminaObjetoBloque),
  path('elimina-objetoconfpersonalizada/<int:id_user>/<slug:nombre_cv>/<slug:cv>/<str:bloque>/<slug:atributo>', views.eliminaObjetoConfiguracionPersonalizada),
  path('informacion_csv/<str:bloque>/<int:idDocente>', views.informacionCsv),
  path('informacion_bibtex/<str:bloque>/<int:idDocente>', views.InformacionBibTex),
  re_path('^personalizacion_usuario/(?P<id_user>.+)/$', views.PersonalizacionUsuario.as_view()),
]