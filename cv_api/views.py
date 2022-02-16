# from codecs import EncodedFile
from django.http.response import JsonResponse
# from django.shortcuts import render
# from numpy import source          
from rest_framework import generics, viewsets
from rest_framework.views import APIView
from django.contrib.auth import login as django_login
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from . import models
from . import serializers
import requests
from django.http import HttpResponse
import pandas as pd
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from django.conf import settings
import json
from datetime import datetime
import csv
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from django.shortcuts import redirect
import urllib.request
import urllib.parse



class ConfiguracionCvView(viewsets.ModelViewSet):
    queryset = models.ConfiguracionCv.objects.all()
    serializer_class = serializers.ConfiguracionCvSerializer


class ConfiguracionCv_PersonalizadoView(viewsets.ModelViewSet):
    queryset = models.ConfiguracionCv_Personalizado.objects.all()
    serializer_class = serializers.ConfiguracionCv_PersonalizadoSerializer


class UsarioView(viewsets.ModelViewSet):
    queryset = models.Usuario.objects.all()
    serializer_class = serializers.UsuarioSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = []
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = serializers.LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        test = serializers.UsuarioSerializer(user)
        django_login(request, user)
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "username": test.data}, status=200)


class BloqueView(viewsets.ModelViewSet):
    queryset = models.Bloque.objects.all()
    serializer_class = serializers.BloqueSerializer
    # permission_classes = [IsAuthenticated]

class ServicioView(viewsets.ModelViewSet):
    queryset = models.Servicio.objects.all()
    serializer_class = serializers.ServicioSerializer
    # permission_classes = [IsAuthenticated]


class PersonalizacionUsuario(generics.ListAPIView):
    serializer_class = serializers.ConfiguracionCv_PersonalizadoSerializer
    def get_queryset(self):
        id_user = self.kwargs['id_user']
        return models.ConfiguracionCv_Personalizado.objects.filter(id_user=id_user)
        


# -------------------------------------------------------GENERACION DE INFORMACION-CONFIGURACION COMPLETA----------------------------------------------
'''OBTIENE INFO CONFIGURACION COMPLETA'''
def InformacionConfCompleto(id):
    model_dict = models.ConfiguracionCv.objects.all().values()
    model_bloques = models.Bloque.objects.all().values()
    model_servicios = models.Servicio.objects.all().values()

    r = requests.get(f'https://sica.utpl.edu.ec/ws/api/docentes/{id}/',
                     headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'})
    docente = r.json()

    listaId = dict()
    temp_data = []
    bloquesLista = []

    for servicio in model_servicios:   
        bloquesLista.append(servicio['url'])
    bloquesLista.sort()


    '''RECORRE BLOQUES'''
    for bloque in bloquesLista: 

        lista_ids = [items['id'] for items in docente['related'][bloque.rsplit('/', 2)[-2]]]

        for id in lista_ids:
            data_tt = requests.get(bloque + str(id) + "/",
                 headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
               )
            temp_data.append(data_tt.json())
        listaId[bloque.rsplit('/', 2)[-2]] = temp_data
        temp_data = []

    bloquesTodos = []
    for bloque in model_bloques:
      bloquesTodos.append(bloque['nombre'])

    bloquesTodos.sort()

    '''Cambia valores None por cadena ('None') '''
    for claveLista, valorLista in listaId.items():
        for valor in valorLista:
          for key, value in valor.items():
            if value is None:
                value = 'None'
            valor[key] = value


    '''BLOQUES DE MODEL BLOQUES ORDENADOS '''
    ordenadosBloques = sorted(
        model_bloques, key=lambda orden: orden['ordenCompleto'])
    bloqueOrdenApi = [{b['nombre']: b['visible_cv_bloqueCompleto']}
                      for b in ordenadosBloques]

    bloqueOrdenApi = [bloqueOrden for bloqueOrden in bloqueOrdenApi if list(bloqueOrden.values()) != [False]]

    listaBloques = [[x for x, v in i.items()] for i in bloqueOrdenApi]
    listaBloquesOrdenados = [y for x in listaBloques for y in x]

    '''SACA VISIBLES SI SON TRUE'''
    diccionario = dict()
    for i in listaBloquesOrdenados:
        visibles = [{'nombre': d['atributo'], 'ordenCompleto': d['ordenCompleto']}
                    for d in model_dict if d.get("visible_cv_completo") and d.get('bloque') == i]
        ordenadosAtributos = sorted(visibles, key=lambda orden: orden['ordenCompleto'])
        listaatrvisibles = [[valor for clave, valor in i.items(
        ) if clave == 'nombre'] for i in ordenadosAtributos]
        listaVisiblesAtr = [y for x in listaatrvisibles for y in x]
        diccionario[i] = listaVisiblesAtr

    bloquesInformacion = dict()
    cont = 0
    for name_bloque, data_bloque in listaId.items():
 
      bloquesInformacion[bloquesTodos[cont]] = data_bloque
      cont+= 1


    '''SACA MAPEO SI ATRIBUTO ES TRUE'''
    listadoBloques = dict()
    listaMapeados = dict()
    

    for i in listaBloquesOrdenados:
        mapeo = [{'mapeo': d['mapeo'], 'ordenCompleto': d['ordenCompleto']} for d in model_dict if d.get(
            "visible_cv_completo") and d.get('bloque') == i]
        ordenadosMapeo = sorted(mapeo, key=lambda orden: orden['ordenCompleto'])

        listamapeoisibles = [[valor for clave, valor in i.items(
        ) if clave == 'mapeo'] for i in ordenadosMapeo]
        listaVisiblesmapeo = [y for x in listamapeoisibles for y in x]

        mapeados = pd.unique(listaVisiblesmapeo)
        listaMapeados[i] = mapeados
        filtrados = [{atributo: d.get(atributo) for atributo in diccionario[i] if d.get(
            atributo) != None} for d in bloquesInformacion[i]]
        listadoBloques[i] = filtrados
 
    bloqueAtributos = dict()
    for listadoBloque in listadoBloques:
        bloqueAtributos[listadoBloque] = [{atributo: d.get(atributo) for atributo in diccionario[listadoBloque] if d.get(
            atributo) != None} for d in bloquesInformacion[listadoBloque]]

    i = []
    for i in listaBloquesOrdenados:
        for filtrado in bloqueAtributos[i]:
            filtrado["mapeo"] = [fil for fil in listaMapeados[i]]

    bloquesInfoRestante = {k: v for k, v in bloqueAtributos.items() if v != []}

    bloquesRestantes = []

    for bloqueInfRes in bloquesInfoRestante:
        bloquesRestantes.append(bloqueInfRes)

    # listaArchivos = []
    listaResultados = []
    listaFinal = list()
    # listaFinalArchivos = list()
    tituloBloque = dict()
    # tituloDic = dict()

    for i in bloquesRestantes:
        tituloBloque['-'] = i.upper()
        # tituloDic =  i.upper()
        listaResultados.append(tituloBloque)
        # listaArchivos.append(tituloDic)
        for bloqueInformacion in bloquesInfoRestante[i]:
            resultados = dict(
                zip(bloqueInformacion['mapeo'], bloqueInformacion.values()))
            listaResultados.append(resultados)
            # listaArchivos.append(resultados)
        listaFinal.append(listaResultados)
        # listaFinalArchivos.append(listaArchivos)
        # listaArchivos = []
        listaResultados = []
        tituloBloque = {}
        # tituloDic = {}

    # print("listaFinalArchivos", listaFinalArchivos)

    return docente, listaFinal


def InformacionCompletaArchivos(bloque, idDocente):
    model_dict = models.ConfiguracionCv.objects.all().values()
    model_bloques = models.Bloque.objects.filter(nombreService = bloque).values()
    # print("BLOQUE", bloque)
    # print("MODELSERVICIOS", model_bloques)

    r = requests.get(f'https://sica.utpl.edu.ec/ws/api/docentes/{idDocente}/',
                     headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'})
    docente = r.json()

    listaId = dict()
    temp_data = []
    
    
    '''RECORRE BLOQUES'''
    lista_ids = [items['id'] for items in docente['related'][bloque]]
    for id in lista_ids:
        data_tt = requests.get(f'https://sica.utpl.edu.ec/ws/api/' + bloque + '/' + str(id) + "/",
             headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
           )
        temp_data.append(data_tt.json())
    listaId[bloque] = temp_data
    temp_data = []

    bloquesTodos = []
    for bloque in model_bloques:
      bloquesTodos.append(bloque['nombreService'])

    bloquesTodos.sort()

    '''Cambia valores None por cadena ('None') '''
    for claveLista, valorLista in listaId.items():
        for valor in valorLista:
          for key, value in valor.items():
            if value is None:
                value = 'None'
            valor[key] = value

    '''BLOQUES DE MODEL BLOQUES ORDENADOS '''
    ordenadosBloques = sorted(
        model_bloques, key=lambda orden: orden['ordenCompleto'])
    bloqueOrdenApi = [{b['nombreService']: b['visible_cv_bloqueCompleto']}
                      for b in ordenadosBloques]

    bloqueOrdenApi = [bloqueOrden for bloqueOrden in bloqueOrdenApi if list(bloqueOrden.values()) != [False]]

    listaBloques = [[x for x, v in i.items()] for i in bloqueOrdenApi]
    listaBloquesOrdenados = [y for x in listaBloques for y in x]

    '''SACA VISIBLES SI SON TRUE'''
    diccionario = dict()
    for i in listaBloquesOrdenados:
        visibles = [{'nombreService': d['atributo'], 'ordenCompleto': d['ordenCompleto']}
                    for d in model_dict if d.get("visible_cv_completo") and d.get('bloqueService') == i]
        ordenadosAtributos = sorted(visibles, key=lambda orden: orden['ordenCompleto'])
        listaatrvisibles = [[valor for clave, valor in i.items(
        ) if clave == 'nombreService'] for i in ordenadosAtributos]
        listaVisiblesAtr = [y for x in listaatrvisibles for y in x]
        diccionario[i] = listaVisiblesAtr

    bloquesInformacion = dict()
    cont = 0
    # try:

    for name_bloque, data_bloque in listaId.items():
    
      bloquesInformacion[bloquesTodos[cont]] = data_bloque
      cont+= 1
  
    # except:
    #     print("ERROR")

    '''SACA MAPEO SI ATRIBUTO ES TRUE'''
    listadoBloques = dict()
    listaMapeados = dict()
    

    
    for i in listaBloquesOrdenados:
        mapeo = [{'mapeo': d['mapeo'], 'ordenCompleto': d['ordenCompleto']} for d in model_dict if d.get(
            "visible_cv_completo") and d.get('bloqueService') == i]
        ordenadosMapeo = sorted(mapeo, key=lambda orden: orden['ordenCompleto'])

        listamapeoisibles = [[valor for clave, valor in i.items(
        ) if clave == 'mapeo'] for i in ordenadosMapeo]
        listaVisiblesmapeo = [y for x in listamapeoisibles for y in x]

        mapeados = pd.unique(listaVisiblesmapeo)
        listaMapeados[i] = mapeados
        filtrados = [{atributo: d.get(atributo) for atributo in diccionario[i] if d.get(
            atributo) != None} for d in bloquesInformacion[i]]
        listadoBloques[i] = filtrados
 
    bloqueAtributos = dict()
    for listadoBloque in listadoBloques:
        bloqueAtributos[listadoBloque] = [{atributo: d.get(atributo) for atributo in diccionario[listadoBloque] if d.get(
            atributo) != None} for d in bloquesInformacion[listadoBloque]]

    i = []
    for i in listaBloquesOrdenados:
        for filtrado in bloqueAtributos[i]:
            filtrado["mapeo"] = [fil for fil in listaMapeados[i]]

    bloquesInfoRestante = {k: v for k, v in bloqueAtributos.items() if v != []}

    bloquesRestantes = []

    for bloqueInfRes in bloquesInfoRestante:
        bloquesRestantes.append(bloqueInfRes)

    listaArchivos = []
    listaResultados = []
    listaFinal = list()
    listaFinalArchivos = list()
    tituloBloque = dict()
    tituloDic = dict()

    for i in bloquesRestantes:
        # tituloBloque['-'] = i.upper()
        tituloDic =  i
        # listaResultados.append(tituloBloque)
        listaArchivos.append(tituloDic)
        for bloqueInformacion in bloquesInfoRestante[i]:
            resultados = dict(
                zip(bloqueInformacion['mapeo'], bloqueInformacion.values()))
            # listaResultados.append(resultados)
            listaArchivos.append(resultados)
        # listaFinal.append(listaResultados)
        listaFinalArchivos.append(listaArchivos)
        listaArchivos = []
        # listaResultados = []
        # tituloBloque = {}
        tituloDic = {}

    return listaFinalArchivos



'''GENERA PDF COMPLETO'''
def PdfCompleto(request, id):
    docente, listaFinal = InformacionConfCompleto(id)

    logo = str(settings.BASE_DIR) + '/cv_api/templates/img/logoutpl.png'
    context = {'logo': logo,
               'docente': docente, 'listaFinal': listaFinal}
    html_string = render_to_string('home_page.html', context)
    html = HTML(string=html_string)
    pdf = html.write_pdf(stylesheets=[CSS(str(settings.BASE_DIR) +
                                          '/cv_api/templates/css/pdf_gen.css')], presentational_hints=True)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="mypdf.pdf"'

    return response


'''DOCUMENTO WORD COMPLETO'''
def DocCompleto(request, id):
    docente, listaFinal = InformacionConfCompleto(id)
    logo = str(settings.BASE_DIR) + '/cv_api/templates/img/logoutpl.png'
    img_template = str(settings.BASE_DIR) + '/cv_api/templates/img/nieve.jpg'
    response = HttpResponse(content_type='application/msword')
    response['Content-Disposition'] = 'attachment; filename="cv.docx"'

    doc = DocxTemplate(str(settings.BASE_DIR) + '/cv_api/templates/docx_filename.docx')
    f = open(str(settings.BASE_DIR) + '/cv_api/templates/img/nieve.jpg','wb')
    f.write(urllib.request.urlopen(docente['foto_web_low']).read()) 

    myimage = InlineImage(doc, image_descriptor=logo, width=Mm(15), height=Mm(25))
    docente_img = InlineImage(doc, img_template, width=Mm(60), height=Mm(60))
    context = {'listaFinal': listaFinal, 'docente': docente, 'var': logo, 'myimage': myimage, 'imagen':docente_img}
    doc.render(context)
    doc.save(response)

    return response


'''GENERA JSON COMPLETO'''
def JsonCompleto(request, id):
    docente, listaFinal = InformacionConfCompleto(id)

    listaDocente = []
    del docente['related']
    listaDocente.append('Docente')
    listaDocente.append(docente)
    listaFinal.append(listaDocente)

    jsonString = json.dumps(listaFinal,  ensure_ascii=False).encode('utf8')
    print(jsonString)
    response = HttpResponse(jsonString.decode(), content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename=export.json'
   
    return response


# -------------------------------------------------------GENERACION DE INFORMACION-CONFIGURACION RESUMIDA----------------------------------------------
def InformacionConfResumida(id):
    model_dict = models.ConfiguracionCv.objects.all().values()
    model_bloques = models.Bloque.objects.all().values()
    model_servicios = models.Servicio.objects.all().values()

    print("MODELSERVICIOS", model_servicios)

    r = requests.get(f'https://sica.utpl.edu.ec/ws/api/docentes/{id}/',
                     headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'})
    docente = r.json()

    listaId = dict()
    temp_data = []
    bloquesLista = []

    for servicio in model_servicios:   
        bloquesLista.append(servicio['url'])
    bloquesLista.sort()

    '''RECORRE BLOQUES'''
    for bloque in bloquesLista: 
        print("ServicioNormal", bloque)
        print("Servicio", bloque.rsplit('/', 2)[-2])

        lista_ids = [items['id'] for items in docente['related'][bloque.rsplit('/', 2)[-2]]]

        for id in lista_ids:
            data_tt = requests.get(bloque + str(id) + "/",
                 headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
               )
            temp_data.append(data_tt.json())
        listaId[bloque.rsplit('/', 2)[-2]] = temp_data
        temp_data = []

    bloquesTodos = []
    for bloque in model_bloques:
      bloquesTodos.append(bloque['nombre'])

    bloquesTodos.sort()

    '''Cambia valores None por cadena ('None') '''
    for claveLista, valorLista in listaId.items():
        for valor in valorLista:
          print(valor)
          for key, value in valor.items():
            if value is None:
                value = 'None'
            valor[key] = value

    '''BLOQUES DE MODEL BLOQUES ORDENADOS '''
    ordenadosBloques = sorted(
        model_bloques, key=lambda orden: orden['ordenResumido'])
    bloqueOrdenApi = [{b['nombre']: b['ordenResumido']}
                      for b in ordenadosBloques]

    bloqueOrdenApi = [bloqueOrden for bloqueOrden in bloqueOrdenApi if list(bloqueOrden.values()) != [0]]

    listaBloques = [[x for x, v in i.items()] for i in bloqueOrdenApi]
    listaBloquesOrdenados = [y for x in listaBloques for y in x]

    '''SACA VISIBLES SI SON TRUE'''
    diccionario = dict()
    for i in listaBloquesOrdenados:
        visibles = [{'nombre': d['atributo'], 'ordenResumido': d['ordenResumido']}
                    for d in model_dict if d.get("visible_cv_resumido") and d.get('bloque') == i]
        ordenadosAtributos = sorted(visibles, key=lambda orden: orden['ordenResumido'])
        listaatrvisibles = [[valor for clave, valor in i.items(
        ) if clave == 'nombre'] for i in ordenadosAtributos]
        listaVisiblesAtr = [y for x in listaatrvisibles for y in x]
        diccionario[i] = listaVisiblesAtr


    bloquesInformacion = dict()
    cont = 0
    for name_bloque, data_bloque in listaId.items():
 
      bloquesInformacion[bloquesTodos[cont]] = data_bloque
      cont+= 1
  
    '''SACA MAPEO SI ATRIBUTO ES TRUE'''
    listadoBloques = dict()
    listaMapeados = dict()
    
    for i in listaBloquesOrdenados:
        mapeo = [{'mapeo': d['mapeo'], 'ordenResumido': d['ordenResumido']} for d in model_dict if d.get(
            "visible_cv_resumido") and d.get('bloque') == i]
        ordenadosMapeo = sorted(mapeo, key=lambda orden: orden['ordenResumido'])

        listamapeoisibles = [[valor for clave, valor in i.items(
        ) if clave == 'mapeo'] for i in ordenadosMapeo]
        listaVisiblesmapeo = [y for x in listamapeoisibles for y in x]

        mapeados = pd.unique(listaVisiblesmapeo)
        listaMapeados[i] = mapeados
        filtrados = [{atributo: d.get(atributo) for atributo in diccionario[i] if d.get(
            atributo) != None} for d in bloquesInformacion[i]]

        listadoBloques[i] = filtrados

    bloqueAtributos = dict()
    for listadoBloque in listadoBloques:
        bloqueAtributos[listadoBloque] = [{atributo: d.get(atributo) for atributo in diccionario[listadoBloque] if d.get(
            atributo) != None} for d in bloquesInformacion[listadoBloque]]

    i = []
    for i in listaBloquesOrdenados:
        for filtrado in bloqueAtributos[i]:
            filtrado["mapeo"] = [fil for fil in listaMapeados[i]]
        
    bloquesInfoRestante = {k: v for k, v in bloqueAtributos.items() if v != []}
    bloquesRestantes = []

    for bloqueInfRes in bloquesInfoRestante:
        bloquesRestantes.append(bloqueInfRes)

    listaResultados = []
    listaFinal = list()
    tituloBloque = dict()
    for i in bloquesRestantes:
        tituloBloque['-'] = i.upper()
        listaResultados.append(tituloBloque)
        for bloqueInformacion in bloquesInfoRestante[i]:
            resultados = dict(
                zip(bloqueInformacion['mapeo'], bloqueInformacion.values()))
            listaResultados.append(resultados)

        listaFinal.append(listaResultados)
        listaResultados = []
        tituloBloque = {}

    return docente, listaFinal


'''GENERA PDF RESUMIDO'''
def PdfResumido(request, id):
    docente, listaFinal = InformacionConfResumida(id)

    '''Generacion de PDF'''
    logo = str(settings.BASE_DIR) + '/cv_api/templates/img/logoutpl.png'
    context = {'logo': logo,
               'docente': docente, 'listaFinal': listaFinal}
    html_string = render_to_string('home_page.html', context)
    html = HTML(string=html_string)
    pdf = html.write_pdf(stylesheets=[CSS(str(settings.BASE_DIR) +
                                          '/cv_api/templates/css/pdf_gen.css')], presentational_hints=True)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="cv_resumido.pdf"'

    return response


'''GENERA DOC RESUMIDO'''
def DocResumido(request, id):
    docente, listaFinal = InformacionConfResumida(id)
    logo = str(settings.BASE_DIR) + '/cv_api/templates/img/logoutpl.png'
    img_template = str(settings.BASE_DIR) + '/cv_api/templates/img/nieve.jpg'
    response = HttpResponse(content_type='application/msword')
    response['Content-Disposition'] = 'attachment; filename="cv_resumido.docx"'

    doc = DocxTemplate(str(settings.BASE_DIR) + '/cv_api/templates/docx_filename.docx')
    f = open(str(settings.BASE_DIR) + '/cv_api/templates/img/nieve.jpg','wb')
    f.write(urllib.request.urlopen(docente['foto_web_low']).read()) 

    myimage = InlineImage(doc, image_descriptor=logo, width=Mm(15), height=Mm(25))
    docente_img = InlineImage(doc, img_template, width=Mm(60), height=Mm(60))
    context = {'listaFinal': listaFinal, 'docente': docente, 'var': logo, 'myimage': myimage, 'imagen':docente_img}

    doc.render(context)
    doc.save(response) 

    return response


'''GENERA JSON RESUMIDO'''
def JsonResumido(request, id):
    
    docente, listaFinal = InformacionConfResumida(id)
    listaDocente = []
    del docente['related']
    listaDocente.append('Docente')
    listaDocente.append(docente)
    listaFinal.append(listaDocente)

    jsonString = json.dumps(listaFinal,  ensure_ascii=False).encode('utf8')
    print(jsonString)
    response = HttpResponse(jsonString.decode(), content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename=export.json'
   
    return response


# -------------------------------------------------------GENERACION DE INFORMACION-CONFIGURACION PERSONALIZADA----------------------------------------------
def InformacionConfPersonalizada(id, nombre_cv, cvHash):
    model_dict = models.ConfiguracionCv_Personalizado.objects.all().values().filter(id_user=id).filter(nombre_cv=nombre_cv).filter(cv=cvHash)
    model_bloques = models.Bloque.objects.all().values()
    model_servicios = models.Servicio.objects.all().values()

    dataPersonalizada = model_dict

    r = requests.get(f'https://sica.utpl.edu.ec/ws/api/docentes/{id}/',
                     headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'})
    docente = r.json()

    listaId = dict()
    temp_data = []
    bloquesLista = []

    for servicio in model_servicios:   
        bloquesLista.append(servicio['url'])
    bloquesLista.sort()

    '''RECORRE BLOQUES'''
    for bloque in bloquesLista: 
        lista_ids = [items['id'] for items in docente['related'][bloque.rsplit('/', 2)[-2]]]
        for id in lista_ids:
            data_tt = requests.get(bloque + str(id) + "/",
                 headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
               )
            temp_data.append(data_tt.json())
        listaId[bloque.rsplit('/', 2)[-2]] = temp_data
        temp_data = []

    bloquesTodos = []

    for bloque in model_bloques:
      bloquesTodos.append(bloque['nombre'])

    bloquesTodos.sort()

    '''Cambia valores None por cadena ('None') '''
    for claveLista, valorLista in listaId.items():
        for valor in valorLista:
        #   print(valor)
          for key, value in valor.items():
            if value is None:
                value = 'None'
            valor[key] = value

    '''BLOQUES DE MODEL BLOQUES ORDENADOS '''
    ordenadosBloquesAPi = sorted(
        dataPersonalizada, key=lambda orden: orden['ordenPersonalizable'])
    bloqueOrdenApi = [{b['bloque']: b['visible_cv_bloque']}
                      for b in ordenadosBloquesAPi]

    seen = set()
    bloquesOrdenados = []
    for d in bloqueOrdenApi:
        t = tuple(d.items())
        if t not in seen:
            seen.add(t)
            bloquesOrdenados.append(d)

    ordenadosBloques = [bloqueOrden for bloqueOrden in bloquesOrdenados if list(bloqueOrden.values()) != [False]]

    listaBloques = [[x for x, v in i.items()] for i in ordenadosBloques]
    listaBloquesOrdenados = [y for x in listaBloques for y in x]

    '''SACA VISIBLES SI SON TRUE'''
    diccionario = dict()
    for i in listaBloquesOrdenados:
        visibles = [{'nombre': d['atributo'], 'orden': d['orden']} for d in dataPersonalizada if d.get(
            "visible_cv_personalizado") and d.get('bloque') == i]
        ordenadosAtributos = sorted(visibles, key=lambda orden: orden['orden'])
        listaatrvisibles = [[valor for clave, valor in i.items(
        ) if clave == 'nombre'] for i in ordenadosAtributos]
        listaVisiblesAtr = [y for x in listaatrvisibles for y in x]

        diccionario[i] = listaVisiblesAtr

    '''SACA MAPEO SI ATRIBUTO ES TRUE'''
    listadoBloques = dict()
    listaMapeados = dict()
    bloquesInformacion = dict()

    cont = 0

    for name_bloque, data_bloque in listaId.items():  
      bloquesInformacion[bloquesTodos[cont]] = data_bloque
      cont+= 1

    for i in listaBloquesOrdenados:
        mapeo = [{'mapeo': d['mapeo'], 'orden': d['orden']} for d in dataPersonalizada if d.get(
            "visible_cv_personalizado") and d.get('bloque') == i]
        ordenadosMapeo = sorted(mapeo, key=lambda orden: orden['orden'])

        listamapeoisibles = [[valor for clave, valor in i.items(
        ) if clave == 'mapeo'] for i in ordenadosMapeo]
        listaVisiblesmapeo = [y for x in listamapeoisibles for y in x]

        mapeados = pd.unique(listaVisiblesmapeo)
        listaMapeados[i] = mapeados
        filtrados = [{atributo: d.get(atributo) for atributo in diccionario[i] if d.get(
            atributo) != None} for d in bloquesInformacion[i]]
        listadoBloques[i] = filtrados

    bloqueAtributos = dict()
    for listadoBloque in listadoBloques:
        bloqueAtributos[listadoBloque] = [{atributo: d.get(atributo) for atributo in diccionario[listadoBloque] if d.get(
            atributo) != None} for d in bloquesInformacion[listadoBloque]]

    bloquesInfoRestante = {k: v for k, v in bloqueAtributos.items() if [
        item for item in v if item != {}]}

    i = []
    for i in listaBloquesOrdenados:
        for filtrado in bloqueAtributos[i]:
            filtrado["mapeo"] = [fil for fil in listaMapeados[i]]
       
    bloquesRestantes = []

    for bloqueInfRes in bloquesInfoRestante:
        bloquesRestantes.append(bloqueInfRes)
 
    listaResultados = []
    listaFinal = list()
    tituloBloque = dict()
    for i in bloquesRestantes:
        tituloBloque['-'] = i.upper()
        listaResultados.append(tituloBloque)
        for bloqueInformacion in bloquesInfoRestante[i]:
            resultados = dict(
                zip(bloqueInformacion['mapeo'], bloqueInformacion.values()))
            listaResultados.append(resultados)

        listaFinal.append(listaResultados)
        listaResultados = []
        tituloBloque = {}

    return docente, listaFinal


'''GENERA PDF PERSONALIZADO'''
def PdfPersonalizado(request, id, nombre_cv, cvHash):
    docente, listaFinal = InformacionConfPersonalizada(id, nombre_cv, cvHash)

    logo = str(settings.BASE_DIR) + '/cv_api/templates/img/logoutpl.png'
    context = {'logo': logo,
               'docente': docente, 'listaFinal': listaFinal}
    html_string = render_to_string('home_page.html', context)
    html = HTML(string=html_string)
    pdf = html.write_pdf(stylesheets=[CSS(str(settings.BASE_DIR) +
                                          '/cv_api/templates/css/pdf_gen.css')], presentational_hints=True)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="cv_personalizado.pdf"'

    return response


'''DOCUMENTO WORD PERSONALIZADO'''
def DocPersonalizado(request, id, nombre_cv, cvHash):
    docente, listaFinal = InformacionConfPersonalizada(id, nombre_cv, cvHash)
    logo = str(settings.BASE_DIR) + '/cv_api/templates/img/logoutpl.png'
    img_template = str(settings.BASE_DIR) + '/cv_api/templates/img/nieve.jpg'

    response = HttpResponse(content_type='application/msword')
    response['Content-Disposition'] = 'attachment; filename="cv_personalizado.docx"'

    doc = DocxTemplate(str(settings.BASE_DIR) + '/cv_api/templates/docx_filename.docx')
    f = open(str(settings.BASE_DIR) + '/cv_api/templates/img/nieve.jpg','wb')
    f.write(urllib.request.urlopen(docente['foto_web_low']).read()) 

    myimage = InlineImage(doc, image_descriptor=logo, width=Mm(15), height=Mm(25))
    docente_img = InlineImage(doc, img_template, width=Mm(60), height=Mm(60))
    context = {'listaFinal': listaFinal, 'docente': docente, 'var': logo, 'myimage': myimage, 'imagen':docente_img}

    doc.render(context)
    doc.save(response) 

    return response


'''GENERACION DE JSON PERSONALIZADO'''
def JsonPersonalizado(request, id, nombre_cv, cvHash):   
    docente, listaFinal = InformacionConfPersonalizada(id, nombre_cv, cvHash)
    listaDocente = []
    del docente['related']
    listaDocente.append('Docente')
    listaDocente.append(docente)
    listaFinal.append(listaDocente)

    jsonString = json.dumps(listaFinal,  ensure_ascii=False).encode('utf8')
    print(jsonString)
    response = HttpResponse(jsonString.decode(), content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename=export.json'
   
    return response


# -------------------------------------------------------GENERACION DE TXT----------------------------------------------
def InformacionTxt(request, bloque, idDocente):

    listaFinalArchivos = InformacionCompletaArchivos(bloque, idDocente)

    listaVacia = []
    try:
        for busqueda in listaFinalArchivos:
          if bloque == busqueda[0]:
            for i in busqueda:
              listaVacia.append(i)

        listaVacia.remove(bloque)
    except:
        print("")

    lines = []

    source = 'SIAC UTPL'
    listaEliminar = ['id', 'authors','abstract', '']
    for articulo in listaVacia:
        fecha = datetime.now()
        variables  = articulo.items()
        lines.append(f'\n\n\n\n{source}\nEXPORT DATE:{fecha}\n')
        for k,v in variables:

            if k == '': 
                diccionario = 'Título' + ':' + str(v)
                lines.append(f'{diccionario}\n')

            if k in listaEliminar:
                print("sdsad")
            else:

                diccionario = k + ":" + str(v)
                lines.append(f'{diccionario}\n')
                diccionario = {}

        lines.append('SOURCE:'f'{source}')

    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename=export.txt'
    response.writelines(lines)

    return response


# -------------------------------------------------------GENERACION DE CSV----------------------------------------------
def informacionCsv(request,bloque, idDocente):
    listaFinalArchivos = InformacionCompletaArchivos(bloque, idDocente)

    listaVacia = []
    try:
        for busqueda in listaFinalArchivos:
          if bloque == busqueda[0]:
            for i in busqueda:
              listaVacia.append(i)

        listaVacia.remove(bloque)
    except:
        print("asdsad")

    response = HttpResponse(content_type='text/csv')  
    response['Content-Disposition'] = 'attachment; filename="file.csv"'  
    writer = csv.writer(response)  

    diccionario = dict()

    lines = []

    source = 'SIAC UTPL'
    listaEliminar = ['id', 'authors','abstract']
    for articulo in listaVacia:
        fecha = datetime.now()
        variables  = articulo.items()
        diccionario
        for k,v in variables:
            if k in listaEliminar :
                print(" ")
            else:
                diccionario[k]= str(v)
        diccionario['source'] = source

        lines.append(diccionario)
        diccionario = {}
    
    for val in lines:
        datos = [k for k, v in val.items()]

    valor = 'Título'
    try:
        writer.writerow([val if val != '' else valor for val in datos])

        for val in lines:
            writer.writerow(v for k, v in val.items())
    except:
        print("ERROR")

    return response  


# -------------------------------------------------------GENERACION DE BIBTEX----------------------------------------------
def InformacionBibTex(request, bloque, idDocente):
    listaFinalArchivos = InformacionCompletaArchivos(bloque, idDocente)
    r = requests.get(f'https://sica.utpl.edu.ec/ws/api/docentes/{idDocente}/',
                     headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'})
    docente = r.json()

    listaVacia = []
    try:
        for busqueda in listaFinalArchivos:
          if bloque == busqueda[0]:
            for i in busqueda:
              listaVacia.append(i)

        listaVacia.remove(bloque)
    except:
        print("")

    diccionario = dict()
    lines = []
    # listaEliminar = ['id', 'authors', 'Año', 'anio']
    for articulo in listaVacia:
        try:
            variables  = articulo.items()
            for k,v in variables:

                diccionario[k]= str(v)

                if k == '':
                    diccionario['Título']= str(v)

                if k == 'Año' :
                    diccionario['ID'] = docente['primer_apellido'] + str(v)

                # if k in listaEliminar :
                #     del diccionario[k]

                if k == '' :
                    del diccionario[k]


            if bloque == 'libros':
                diccionario['ENTRYTYPE'] = 'book'
            
            if bloque =='articulos':
                diccionario['ENTRYTYPE'] = 'article'
            
            if bloque == 'grado-academico':
                diccionario['ENTRYTYPE'] = 'academic'

            if bloque == 'capacitacion':
                diccionario['ENTRYTYPE'] = 'capacitation'

            if bloque == 'tesis':
                diccionario['ENTRYTYPE'] = 'tesis'

            if bloque == 'proyectos':
                diccionario['ENTRYTYPE'] = 'project'

        except:
            print(" ")

        lines.append(diccionario)
        diccionario = {}

    response = BibDatabase()
    response.entries = lines
    writer = BibTexWriter()
    data = writer.write(response)
    response = HttpResponse(data, content_type='text/x-bibtex')  
    response['Content-Disposition'] = 'attachment; filename="file.bib"' 

    return response


def eliminaPersonalizados(request, nombre_cv, cv ):
    model_dict = models.ConfiguracionCv_Personalizado.objects.filter(nombre_cv = nombre_cv).filter(cv=cv)
    model_dict.delete()
    return redirect('/api')


def eliminaObjetoConfiguracion(request, bloque, atributo):
    model_dict = models.ConfiguracionCv.objects.filter(bloque = bloque).filter(atributo=atributo)
    # print("ELIMINADO", model_dict)
    model_dict.delete()
    return redirect('/api')


def eliminaObjetoBloque(request, bloque):
    model_dict = models.Bloque.objects.filter(nombre = bloque)
    model_dict.delete()
    return redirect('/api')


def eliminaObjetoConfiguracionPersonalizada(request, id_user, nombre_cv, cv, bloque, atributo):
    model_dict = models.ConfiguracionCv_Personalizado.objects.filter(id_user = id_user).filter(
        nombre_cv = nombre_cv).filter(cv=cv).filter(bloque=bloque).filter(atributo=atributo)
    model_dict.delete()
    return redirect('/api')
