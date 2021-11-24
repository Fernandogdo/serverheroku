from django.http import response
from django.http.response import JsonResponse
from django.shortcuts import render
import docx
from rest_framework import generics, viewsets
from rest_framework.views import APIView
from django.contrib.auth import login as django_login, logout as django_logout
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from .serializers import ConfiguracionCv_PersonalizadoSerializer, LoginSerializer

from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .serializers import DocenteSerializer
# Create your views here.

from . import models
from . import serializers
import requests
from django.http import HttpResponse

import pandas as pd
from django.template.loader import get_template
from django.template import Context
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from django.conf import settings
#from htmldocx import HtmlToDocx
from docx import Document
from docx.opc.part import Part
from docx.opc.constants import RELATIONSHIP_TYPE as RT
import json
from pathlib import Path
from django.shortcuts import render
import json
from datetime import datetime
import csv
from django.http import FileResponse
#from htmldocx import HtmlToDocx
from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase


class AdministradorView(viewsets.ModelViewSet):
    queryset = models.Administrador.objects.all()
    serializer_class = serializers.AdministradorSerializer


class ConfiguracionCvView(viewsets.ModelViewSet):

    queryset = models.ConfiguracionCv.objects.all()
    serializer_class = serializers.ConfiguracionCvSerializer


class ConfiguracionCv_PersonalizadoView(viewsets.ModelViewSet):

    queryset = models.ConfiguracionCv_Personalizado.objects.all()
    serializer_class = serializers.ConfiguracionCv_PersonalizadoSerializer


class DocenteView(viewsets.ModelViewSet):
    queryset = models.Docente.objects.all()
    serializer_class = serializers.DocenteSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = []
        else:
            permission_classes = [IsAdminUser]
        return [permission() for permission in permission_classes]


class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        test = DocenteSerializer(user)
        django_login(request, user)
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "username": test.data}, status=200)


class BloqueView(viewsets.ModelViewSet):
    queryset = models.Bloque.objects.all()
    serializer_class = serializers.BloqueSerializer


class PersonalizacionUsuario(generics.ListAPIView):
    serializer_class = ConfiguracionCv_PersonalizadoSerializer
    # queryset = models.ConfiguracionCv_Personalizado.objects.all()

    def get_queryset(self):
        id_user = self.kwargs['id_user']
        return models.ConfiguracionCv_Personalizado.objects.filter(id_user=id_user)


def getdata(self):
    id_user = self.kwargs['id_user']
    return models.ConfiguracionCv_Personalizado.objects.filter(id_user=id_user)


# -------------------------------------------------------GENERACION DE DOCUMENTOS PDF----------------------------------------------

'''GENERA PDF COMPLETO'''
def PdfCompleto(request, id):

    model_dict = models.ConfiguracionCv.objects.all().values()
    model_bloques = models.Bloque.objects.all().values()

    r = requests.get(f'https://sica.utpl.edu.ec/ws/api/docentes/{id}/',
                     headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'})
    docente = r.json()

    '''Saca id Articulos '''
    listaidArticulos = []
    for infobloque in docente['related']['articulos']:
        listaidArticulos.append(infobloque)

    idsArticulos = [fila['id'] for fila in listaidArticulos]

    '''Saca id Libros '''
    listaidLibros = []
    for infoLibros in docente['related']['libros']:
        listaidLibros.append(infoLibros)

    idsLibros = [fila['id'] for fila in listaidLibros]

    ''' Saca articulos de docentes por ID'''
    listaArticulosDocente = []
    for id in idsArticulos:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/articulos/' + str(id) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaArticulosDocente.append(todos)
    #   print('listaArticulosDocente------------>>>>>>>>>>>>>>>>>',listaArticulosDocente)

    ''' Saca libros de docentes por ID'''
    listaLibrosDocente = []
    for idLibro in idsLibros:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/libros/' + str(idLibro) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaLibrosDocente.append(todos)
        # print('listaArticulosDocente------------>>>>>>>>>>>>>>>>>',listaLibrosDocente)

    '''Cambia valores None por cadena ('None') '''
    for i in listaLibrosDocente:
        for key, value in i.items():
            if value is None:
                value = 'None'
            i[key] = value

    proyectos = []
    Capacitacion = []
    # ArticulosAutores = []
    # LibrosAutores = []
    GradoAcademico = []
    # ProyectosParticipantes = []

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

    '''SACA MAPEO SI ATRIBUTO ES TRUE'''
    listadoBloques = dict()
    listaMapeados = dict()
    bloquesInformacion = dict()

    '''Tendria que recuperar los bloques que estan como visibles'''
    bloquesInformacion['Articulos'] = listaArticulosDocente
    bloquesInformacion['Proyectos'] = proyectos
    bloquesInformacion['Capacitacion'] = Capacitacion
    bloquesInformacion['Libros'] = listaLibrosDocente
    bloquesInformacion['GradoAcademico'] = GradoAcademico

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
    # print('listaMapeados--->>>>>', listaMapeados)
    # print('filtrados->>>>>>>>>>>>>>>>>>>>>>>', listadoBloques)
    # print('listaMapeados--->>>>>', listaMapeados)
    # print('filtrados->>>>>>>>>>>>>>>>>>>>>>>', listadoBloques)

    bloqueAtributos = dict()
    for listadoBloque in listadoBloques:
        bloqueAtributos[listadoBloque] = [{atributo: d.get(atributo) for atributo in diccionario[listadoBloque] if d.get(
            atributo) != None} for d in bloquesInformacion[listadoBloque]]

    i = []
    for i in listaBloquesOrdenados:
        for filtrado in bloqueAtributos[i]:
            filtrado["mapeo"] = [fil for fil in listaMapeados[i]]
            # filtrado["orden"] = [filtrado for filtrado in mapeados]
    # print('bloqueAtributos----___>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>',bloqueAtributos)

    bloquesInfoRestante = {k: v for k, v in bloqueAtributos.items() if v != []}
    # print('loquesquedan---------__>>>>>>>>>>>>', bloquesInfoRestante)

    bloquesRestantes = []

    for bloqueInfRes in bloquesInfoRestante:
        bloquesRestantes.append(bloqueInfRes)
    # print('listadoBloques-----------__>>>>>>>>>>>>>>>>>',listadoBloques)
    # print(bloquesRestantes)

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

    # print(listaFinal)
    prueba(docente, listaFinal)

    '''Generacion de PDF'''
    logo = str(settings.BASE_DIR) + '/cv_api/templates/logoutpl.png'
    context = {'datos': listaResultados, 'logo': logo,
               'docente': docente, 'listaFinal': listaFinal}
    html_string = render_to_string('home_page.html', context)
    html = HTML(string=html_string)
    pdf = html.write_pdf(stylesheets=[CSS(str(settings.BASE_DIR) +
                                          '/cv_api/templates/css/pdf_gen.css')], presentational_hints=True)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="mypdf.pdf"'

    return response

def prueba(docente, listaFinal):
    print("listaResultadosPRUEBA", listaFinal)

    logo = str(settings.BASE_DIR) + '/cv_api/templates/logoutpl.png'
    context = {'logo': logo,
               'docente': docente, 'listaFinal': listaFinal}
    html_string = render_to_string('home_page.html', context)
    html = HTML(string=html_string)
    pdf = html.write_pdf(stylesheets=[CSS(str(settings.BASE_DIR) +
                                          '/cv_api/templates/css/pdf_gen.css')], presentational_hints=True)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="mypdf.pdf"'

    return response


'''GENERA PDF RESUMIDO'''
def PdfResumido(request, id):

    model_dict = models.ConfiguracionCv.objects.all().values()
    # print('model_dict',model_dict)
    model_bloques = models.Bloque.objects.all().values()

    r = requests.get(f'https://sica.utpl.edu.ec/ws/api/docentes/{id}/',
                     headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'})
    docente = r.json()

    '''Saca id Articulos '''
    listaidArticulos = []
    for infobloque in docente['related']['articulos']:
        listaidArticulos.append(infobloque)

    idsArticulos = [fila['id'] for fila in listaidArticulos]

    '''Saca id Libros '''
    listaidLibros = []
    for infoLibros in docente['related']['libros']:
        listaidLibros.append(infoLibros)

    idsLibros = [fila['id'] for fila in listaidLibros]

    ''' Saca articulos de docentes por ID'''
    listaArticulosDocente = []
    for id in idsArticulos:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/articulos/' + str(id) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaArticulosDocente.append(todos)
    #   print('listaArticulosDocente------------>>>>>>>>>>>>>>>>>',listaArticulosDocente)

    ''' Saca libros de docentes por ID'''
    listaLibrosDocente = []
    for idLibro in idsLibros:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/libros/' + str(idLibro) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaLibrosDocente.append(todos)
        # print('listaArticulosDocente------------>>>>>>>>>>>>>>>>>',listaLibrosDocente)

    '''Cambia valores None por cadena ('None') '''
    for i in listaLibrosDocente:
        for key, value in i.items():
            if value is None:
                value = 'None'
            i[key] = value

    proyectos = []
    Capacitacion = []
    GradoAcademico = []

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

    '''SACA MAPEO SI ATRIBUTO ES TRUE'''
    listadoBloques = dict()
    listaMapeados = dict()
    bloquesInformacion = dict()

    '''Tendria que recuperar los bloques que estan como visibles'''
    bloquesInformacion['Articulos'] = listaArticulosDocente
    bloquesInformacion['Proyectos'] = proyectos
    bloquesInformacion['Capacitacion'] = Capacitacion
    bloquesInformacion['Libros'] = listaLibrosDocente
    bloquesInformacion['GradoAcademico'] = GradoAcademico

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
        # print('filtrados---___________>>>>>>>>>>>>>>>>>>>',filtrados)

        listadoBloques[i] = filtrados

    bloqueAtributos = dict()
    for listadoBloque in listadoBloques:
        bloqueAtributos[listadoBloque] = [{atributo: d.get(atributo) for atributo in diccionario[listadoBloque] if d.get(
            atributo) != None} for d in bloquesInformacion[listadoBloque]]

    i = []
    for i in listaBloquesOrdenados:
        for filtrado in bloqueAtributos[i]:
            filtrado["mapeo"] = [fil for fil in listaMapeados[i]]
            # filtrado["orden"] = [filtrado for filtrado in mapeados]
    # print('bloqueAtributos----___>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>',bloqueAtributos)

    bloquesInfoRestante = {k: v for k, v in bloqueAtributos.items() if v != []}
    # print('loquesquedan---------__>>>>>>>>>>>>', bloquesInfoRestante)

    bloquesRestantes = []

    for bloqueInfRes in bloquesInfoRestante:
        bloquesRestantes.append(bloqueInfRes)
    # print('listadoBloques-----------__>>>>>>>>>>>>>>>>>',listadoBloques)
    # print(bloquesRestantes)

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

    '''Generacion de PDF'''
    logo = str(settings.BASE_DIR) + '/cv_api/templates/logoutpl.png'
    context = {'datos': listaResultados, 'logo': logo,
               'docente': docente, 'listaFinal': listaFinal}
    html_string = render_to_string('home_page.html', context)
    html = HTML(string=html_string)
    pdf = html.write_pdf(stylesheets=[CSS(str(settings.BASE_DIR) +
                                          '/cv_api/templates/css/pdf_gen.css')], presentational_hints=True)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="cv_resumido.pdf"'

    return response




'''GENERA PDF PERSONALIZADO'''
def PdfPersonalizado(request, id, nombre_cv, cvHash):

    # nombre_cv = 'data'
    model_dict = models.ConfiguracionCv_Personalizado.objects.all().values().filter(id_user=id).filter(nombre_cv=nombre_cv).filter(cv=cvHash)
    # print('model_dictPersonalizadolala', model_dict.filter(id_user=4).filter(nombre_cv = nombre_cv))
    # dataFilterId = model_dict.filter(id_user=id)

    # print('model_ditct--------------____>>>>>>>>>>>>>>>>>>>>>>>', dataFilterId)
    # dataHash = dataFilterId.filter(cv=cvHash)
    # print('model_ditct--------------____>>>>>>>>>>>>>>>>>>>>>>>', dataHash)


    dataPersonalizada = model_dict
    

    print('DATAPERSONALIZADA--------------____>>>>>>>>>>>>>>>>>>>>>>>', dataPersonalizada)
    # print('NOMBRECV--------------____>>>>>>>>>>>>>>>>>>>>>>>', dataPersonalizada)

    # model_bloques = models.Bloque.objects.all().values()

    r = requests.get(f'https://sica.utpl.edu.ec/ws/api/docentes/{id}/',
                     headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'})
    docente = r.json()

    '''Saca id Articulos '''
    listaidArticulos = []
    for infobloque in docente['related']['articulos']:
        listaidArticulos.append(infobloque)

    idsArticulos = [fila['id'] for fila in listaidArticulos]

    '''Saca id Libros '''
    listaidLibros = []
    for infoLibros in docente['related']['libros']:
        listaidLibros.append(infoLibros)

    idsLibros = [fila['id'] for fila in listaidLibros]

    ''' Saca articulos de docentes por ID'''
    listaArticulosDocente = []
    for id in idsArticulos:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/articulos/' + str(id) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaArticulosDocente.append(todos)
    #   print('listaArticulosDocente------------>>>>>>>>>>>>>>>>>',listaArticulosDocente)

    ''' Saca libros de docentes por ID'''
    listaLibrosDocente = []
    for idLibro in idsLibros:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/libros/' + str(idLibro) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaLibrosDocente.append(todos)
        # print('listaArticulosDocente------------>>>>>>>>>>>>>>>>>',listaLibrosDocente)

    '''Cambia valores None por cadena ('None') '''
    for i in listaLibrosDocente:
        for key, value in i.items():
            if value is None:
                value = 'None'
            i[key] = value

    proyectos = []
    Capacitacion = []
    GradoAcademico = []

    '''BLOQUES DE MODEL BLOQUES ORDENADOS '''
    ordenadosBloquesAPi = sorted(
        dataPersonalizada, key=lambda orden: orden['ordenPersonalizable'])
    # print("ORDENADOSBLOQUESORIGINAL--------------->>>>>>>>>>>", ordenadosBloquesAPi)

    bloqueOrdenApi = [{b['nombreBloque']: b['visible_cv_bloque']}
                      for b in ordenadosBloquesAPi]

    # print("ORDENADOSBLOQUESORIGINALORDENAPI------->>>>>>>>>>>", bloqueOrdenApi)
    # ordenadosBloquesApi = sorted(bloqueOrdenApi, key=lambda orden: orden["ordenPersonalizable"])
    # print("ORDENADOSBLOQUESAPI------->>>>>>>>>>>", ordenadosBloquesApi)

    seen = set()
    bloquesOrdenados = []
    for d in bloqueOrdenApi:
        t = tuple(d.items())
        if t not in seen:
            seen.add(t)
            bloquesOrdenados.append(d)


    ordenadosBloques = [bloqueOrden for bloqueOrden in bloquesOrdenados if list(bloqueOrden.values()) != [False]]
    # print("ordenadosBloques------->>>>>>>>>>>", ordenadosBloques)

    listaBloques = [[x for x, v in i.items()] for i in ordenadosBloques]
    listaBloquesOrdenados = [y for x in listaBloques for y in x]
    # print("listaBloquesOrdenados------------_______>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", listaBloquesOrdenados)

    '''SACA VISIBLES SI SON TRUE'''
    diccionario = dict()
    for i in listaBloquesOrdenados:
        visibles = [{'nombre': d['atributo'], 'orden': d['orden']} for d in dataPersonalizada if d.get(
            "visible_cv_personalizado") and d.get('bloque') == i]
        ordenadosAtributos = sorted(visibles, key=lambda orden: orden['orden'])
        listaatrvisibles = [[valor for clave, valor in i.items(
        ) if clave == 'nombre'] for i in ordenadosAtributos]
        listaVisiblesAtr = [y for x in listaatrvisibles for y in x]
        # print('listaatrvisibles', listaVisiblesAtr, '\n')  

        diccionario[i] = listaVisiblesAtr

    '''SACA MAPEO SI ATRIBUTO ES TRUE'''
    listadoBloques = dict()
    listaMapeados = dict()
    bloquesInformacion = dict()

    '''Tendria que recuperar los bloques que estan como visibles'''
    bloquesInformacion['Articulos'] = listaArticulosDocente
    bloquesInformacion['Proyectos'] = proyectos
    bloquesInformacion['Capacitacion'] = Capacitacion
    bloquesInformacion['Libros'] = listaLibrosDocente
    bloquesInformacion['GradoAcademico'] = GradoAcademico

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
        # print('filtrados---___________>>>>>>>>>>>>>>>>>>>',i, filtrados)
        listadoBloques[i] = filtrados

    bloqueAtributos = dict()
    for listadoBloque in listadoBloques:
        bloqueAtributos[listadoBloque] = [{atributo: d.get(atributo) for atributo in diccionario[listadoBloque] if d.get(
            atributo) != None} for d in bloquesInformacion[listadoBloque]]
    # print('filtrados->>>>>>>>>>>>>>>>>>>>>>>', bloqueAtributos)

    bloquesInfoRestante = {k: v for k, v in bloqueAtributos.items() if [
        item for item in v if item != {}]}
    # print('bloquesInfoRestante', bloquesInfoRestante)

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

    '''Generacion de PDF'''
    logo = str(settings.BASE_DIR) + '/cv_api/templates/logoutpl.png'
    context = {'datos': listaResultados, 'logo': logo,
               'docente': docente, 'listaFinal': listaFinal}
    html_string = render_to_string('home_page.html', context)
    html = HTML(string=html_string)
    pdf = html.write_pdf(stylesheets=[CSS(str(settings.BASE_DIR) +
                                          '/cv_api/templates/css/pdf_gen.css')], presentational_hints=True)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="cv_personalizado.pdf"'

    return response




# -------------------------------------------------------GENERACION DE DOCUMENTOS WORD----------------------------------------------


'''GENERACION DE DOCUMENTOS WORD'''

'''DOCUMENTO WORD COMPLETO'''
def DocCompleto(request, id):
    model_dict = models.ConfiguracionCv.objects.all().values()
    model_bloques = models.Bloque.objects.all().values()

    r = requests.get(f'https://sica.utpl.edu.ec/ws/api/docentes/{id}/',
                     headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'})
    docente = r.json()
    print(docente)

    '''Saca id Articulos '''
    listaidArticulos = []
    for infobloque in docente['related']['articulos']:
        listaidArticulos.append(infobloque)

    idsArticulos = [fila['id'] for fila in listaidArticulos]

    '''Saca id Libros '''
    listaidLibros = []
    for infoLibros in docente['related']['libros']:
        listaidLibros.append(infoLibros)

    idsLibros = [fila['id'] for fila in listaidLibros]

    ''' Saca articulos de docentes por ID'''
    listaArticulosDocente = []
    for id in idsArticulos:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/articulos/' + str(id) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaArticulosDocente.append(todos)

    ''' Saca libros de docentes por ID'''
    listaLibrosDocente = []
    for idLibro in idsLibros:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/libros/' + str(idLibro) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaLibrosDocente.append(todos)

    '''Cambia valores None por cadena ('None') '''
    for i in listaLibrosDocente:
        for key, value in i.items():
            if value is None:
                value = 'None'
            i[key] = value

    proyectos = []
    Capacitacion = []
    GradoAcademico = []

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

    '''SACA MAPEO SI ATRIBUTO ES TRUE'''
    listadoBloques = dict()
    listaMapeados = dict()
    bloquesInformacion = dict()

    '''Tendria que recuperar los bloques que estan como visibles'''
    bloquesInformacion['Articulos'] = listaArticulosDocente
    bloquesInformacion['Proyectos'] = proyectos
    bloquesInformacion['Capacitacion'] = Capacitacion
    bloquesInformacion['Libros'] = listaLibrosDocente
    bloquesInformacion['GradoAcademico'] = GradoAcademico

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


    logo = str(settings.BASE_DIR) + '/cv_api/templates/logoutpl.png'
    nieve = str(settings.BASE_DIR) + '/cv_api/templates/nieve.jpg'
    response = HttpResponse(content_type='application/msword')
    response['Content-Disposition'] = 'attachment; filename="cv.docx"'

    doc = DocxTemplate(str(settings.BASE_DIR) + '/cv_api/templates/docx_filename.docx')
    imagen = docente['foto_web_low'] 
    # doc.replace_pic('dummy_header_pic.jpg','header_pic_i_want.jpg')
    myimage = InlineImage(doc, image_descriptor=logo, width=Mm(15), height=Mm(25))
    # doc.replace_pic(myimage, nieve)
    context = {'listaFinal': listaFinal, 'docente': docente, 'var': logo, 'myimage': myimage}
  
    doc.render(context)
    doc.save(response)

    return response


'''DOCUMENTO WORD RESUMIDO'''
def DocResumido(request, id):
    model_dict = models.ConfiguracionCv.objects.all().values()
    model_bloques = models.Bloque.objects.all().values()

    r = requests.get(f'https://sica.utpl.edu.ec/ws/api/docentes/{id}/',
                     headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'})
    docente = r.json()

    '''Saca id Articulos '''
    listaidArticulos = []
    for infobloque in docente['related']['articulos']:
        listaidArticulos.append(infobloque)

    idsArticulos = [fila['id'] for fila in listaidArticulos]

    '''Saca id Libros '''
    listaidLibros = []
    for infoLibros in docente['related']['libros']:
        listaidLibros.append(infoLibros)

    idsLibros = [fila['id'] for fila in listaidLibros]

    ''' Saca articulos de docentes por ID'''
    listaArticulosDocente = []
    for id in idsArticulos:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/articulos/' + str(id) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaArticulosDocente.append(todos)
    #   print('listaArticulosDocente------------>>>>>>>>>>>>>>>>>',listaArticulosDocente)

    ''' Saca libros de docentes por ID'''
    listaLibrosDocente = []
    for idLibro in idsLibros:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/libros/' + str(idLibro) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaLibrosDocente.append(todos)
        # print('listaArticulosDocente------------>>>>>>>>>>>>>>>>>',listaLibrosDocente)

    '''Cambia valores None por cadena ('None') '''
    for i in listaLibrosDocente:
        for key, value in i.items():
            if value is None:
                value = 'None'
            i[key] = value

    proyectos = []
    Capacitacion = []
    GradoAcademico = []

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

    '''SACA MAPEO SI ATRIBUTO ES TRUE'''
    listadoBloques = dict()
    listaMapeados = dict()
    bloquesInformacion = dict()

    '''Tendria que recuperar los bloques que estan como visibles'''
    bloquesInformacion['Articulos'] = listaArticulosDocente
    bloquesInformacion['Proyectos'] = proyectos
    bloquesInformacion['Capacitacion'] = Capacitacion
    bloquesInformacion['Libros'] = listaLibrosDocente
    bloquesInformacion['GradoAcademico'] = GradoAcademico

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
        # print('filtrados---___________>>>>>>>>>>>>>>>>>>>',filtrados)

        listadoBloques[i] = filtrados

    bloqueAtributos = dict()
    for listadoBloque in listadoBloques:
        bloqueAtributos[listadoBloque] = [{atributo: d.get(atributo) for atributo in diccionario[listadoBloque] if d.get(
            atributo) != None} for d in bloquesInformacion[listadoBloque]]

    i = []
    for i in listaBloquesOrdenados:
        for filtrado in bloqueAtributos[i]:
            filtrado["mapeo"] = [fil for fil in listaMapeados[i]]
            # filtrado["orden"] = [filtrado for filtrado in mapeados]
    # print('bloqueAtributos----___>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>',bloqueAtributos)

    bloquesInfoRestante = {k: v for k, v in bloqueAtributos.items() if v != []}
    # print('loquesquedan---------__>>>>>>>>>>>>', bloquesInfoRestante)

    bloquesRestantes = []

    for bloqueInfRes in bloquesInfoRestante:
        bloquesRestantes.append(bloqueInfRes)
    # print('listadoBloques-----------__>>>>>>>>>>>>>>>>>',listadoBloques)
    # print(bloquesRestantes)

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

    logo = str(settings.BASE_DIR) + '/cv_api/templates/logoutpl.png'
    response = HttpResponse(content_type='application/msword')
    response['Content-Disposition'] = 'attachment; filename="cv.docx"'

    doc = DocxTemplate(str(settings.BASE_DIR) + '/cv_api/templates/docx_filename.docx')
    imagen = docente['foto_web_low'] 
    myimage = InlineImage(doc, image_descriptor=logo, width=Mm(15), height=Mm(20))
    context = {'listaFinal': listaFinal, 'docente': docente, 'var': logo, 'myimage': myimage}
    doc.render(context)
    doc.save(response) 

    return response


def DocPersonalizado(request, id, nombre_cv, cvHash):
    model_dict = models.ConfiguracionCv_Personalizado.objects.all().values().filter(
    id_user=id).filter(
    nombre_cv=nombre_cv).filter(
    cv=cvHash)

    dataPersonalizada = model_dict

    print('DATAPERSONALIZADA--------------____>>>>>>>>>>>>>>>>>>>>>>>', dataPersonalizada)
    # print('NOMBRECV--------------____>>>>>>>>>>>>>>>>>>>>>>>', dataPersonalizada)

    # model_bloques = models.Bloque.objects.all().values()

    r = requests.get(f'https://sica.utpl.edu.ec/ws/api/docentes/{id}/',
                     headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'})
    docente = r.json()

    '''Saca id Articulos '''
    listaidArticulos = []
    for infobloque in docente['related']['articulos']:
        listaidArticulos.append(infobloque)

    idsArticulos = [fila['id'] for fila in listaidArticulos]

    '''Saca id Libros '''
    listaidLibros = []
    for infoLibros in docente['related']['libros']:
        listaidLibros.append(infoLibros)

    idsLibros = [fila['id'] for fila in listaidLibros]

    ''' Saca articulos de docentes por ID'''
    listaArticulosDocente = []
    for id in idsArticulos:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/articulos/' + str(id) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaArticulosDocente.append(todos)
    #   print('listaArticulosDocente------------>>>>>>>>>>>>>>>>>',listaArticulosDocente)

    ''' Saca libros de docentes por ID'''
    listaLibrosDocente = []
    for idLibro in idsLibros:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/libros/' + str(idLibro) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaLibrosDocente.append(todos)
        # print('listaArticulosDocente------------>>>>>>>>>>>>>>>>>',listaLibrosDocente)

    '''Cambia valores None por cadena ('None') '''
    for i in listaLibrosDocente:
        for key, value in i.items():
            if value is None:
                value = 'None'
            i[key] = value

    proyectos = []
    Capacitacion = []
    GradoAcademico = []

    '''BLOQUES DE MODEL BLOQUES ORDENADOS '''
    ordenadosBloquesAPi = sorted(
        dataPersonalizada, key=lambda orden: orden['ordenPersonalizable'])
    # print("ORDENADOSBLOQUESORIGINAL--------------->>>>>>>>>>>", ordenadosBloquesAPi)

    bloqueOrdenApi = [{b['nombreBloque']: b['visible_cv_bloque']}
                      for b in ordenadosBloquesAPi]

    # print("ORDENADOSBLOQUESORIGINALORDENAPI------->>>>>>>>>>>", bloqueOrdenApi)
    # ordenadosBloquesApi = sorted(bloqueOrdenApi, key=lambda orden: orden["ordenPersonalizable"])
    # print("ORDENADOSBLOQUESAPI------->>>>>>>>>>>", ordenadosBloquesApi)

    seen = set()
    bloquesOrdenados = []
    for d in bloqueOrdenApi:
        t = tuple(d.items())
        if t not in seen:
            seen.add(t)
            bloquesOrdenados.append(d)


    ordenadosBloques = [bloqueOrden for bloqueOrden in bloquesOrdenados if list(bloqueOrden.values()) != [False]]
    # print("ordenadosBloques------->>>>>>>>>>>", ordenadosBloques)

    listaBloques = [[x for x, v in i.items()] for i in ordenadosBloques]
    listaBloquesOrdenados = [y for x in listaBloques for y in x]
    # print("listaBloquesOrdenados------------_______>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", listaBloquesOrdenados)

    '''SACA VISIBLES SI SON TRUE'''
    diccionario = dict()
    for i in listaBloquesOrdenados:
        visibles = [{'nombre': d['atributo'], 'orden': d['orden']} for d in dataPersonalizada if d.get(
            "visible_cv_personalizado") and d.get('bloque') == i]
        ordenadosAtributos = sorted(visibles, key=lambda orden: orden['orden'])
        listaatrvisibles = [[valor for clave, valor in i.items(
        ) if clave == 'nombre'] for i in ordenadosAtributos]
        listaVisiblesAtr = [y for x in listaatrvisibles for y in x]
        # print('listaatrvisibles', listaVisiblesAtr, '\n')  

        diccionario[i] = listaVisiblesAtr

    '''SACA MAPEO SI ATRIBUTO ES TRUE'''
    listadoBloques = dict()
    listaMapeados = dict()
    bloquesInformacion = dict()

    '''Tendria que recuperar los bloques que estan como visibles'''
    bloquesInformacion['Articulos'] = listaArticulosDocente
    bloquesInformacion['Proyectos'] = proyectos
    bloquesInformacion['Capacitacion'] = Capacitacion
    bloquesInformacion['Libros'] = listaLibrosDocente
    bloquesInformacion['GradoAcademico'] = GradoAcademico

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
        # print('filtrados---___________>>>>>>>>>>>>>>>>>>>',i, filtrados)
        listadoBloques[i] = filtrados

    bloqueAtributos = dict()
    for listadoBloque in listadoBloques:
        bloqueAtributos[listadoBloque] = [{atributo: d.get(atributo) for atributo in diccionario[listadoBloque] if d.get(
            atributo) != None} for d in bloquesInformacion[listadoBloque]]
    # print('filtrados->>>>>>>>>>>>>>>>>>>>>>>', bloqueAtributos)

    bloquesInfoRestante = {k: v for k, v in bloqueAtributos.items() if [
        item for item in v if item != {}]}
    # print('bloquesInfoRestante', bloquesInfoRestante)

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

    logo = str(settings.BASE_DIR) + '/cv_api/templates/logoutpl.png'
    response = HttpResponse(content_type='application/msword')
    response['Content-Disposition'] = 'attachment; filename="cv.docx"'

    doc = DocxTemplate(str(settings.BASE_DIR) + '/cv_api/templates/docx_filename.docx')
    imagen = docente['foto_web_low'] 
    myimage = InlineImage(doc, image_descriptor=logo, width=Mm(15), height=Mm(20))
    context = {'listaFinal': listaFinal, 'docente': docente, 'var': logo, 'myimage': myimage}
    doc.render(context)
    doc.save(response) 

    return response


'''GENERA JSON COMPLETO'''
def JsonCompleto(request, id):
    model_dict = models.ConfiguracionCv.objects.all().values()
    model_bloques = models.Bloque.objects.all().values()

    r = requests.get(f'https://sica.utpl.edu.ec/ws/api/docentes/{id}/',
                     headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'})
    docente = r.json()

    '''Saca id Articulos '''
    listaidArticulos = []
    for infobloque in docente['related']['articulos']:
        listaidArticulos.append(infobloque)

    idsArticulos = [fila['id'] for fila in listaidArticulos]

    '''Saca id Libros '''
    listaidLibros = []
    for infoLibros in docente['related']['libros']:
        listaidLibros.append(infoLibros)

    idsLibros = [fila['id'] for fila in listaidLibros]

    ''' Saca articulos de docentes por ID'''
    listaArticulosDocente = []
    for id in idsArticulos:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/articulos/' + str(id) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaArticulosDocente.append(todos)

    ''' Saca libros de docentes por ID'''
    listaLibrosDocente = []
    for idLibro in idsLibros:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/libros/' + str(idLibro) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaLibrosDocente.append(todos)
        # print('listaArticulosDocente------------>>>>>>>>>>>>>>>>>',listaLibrosDocente)

    '''Cambia valores None por cadena ('None') '''
    for i in listaLibrosDocente:
        for key, value in i.items():
            if value is None:
                value = 'None'
            i[key] = value

    proyectos = []
    Capacitacion = []
    GradoAcademico = []

    '''BLOQUES DE MODEL BLOQUES ORDENADOS '''
    ordenadosBloques = sorted(
        model_bloques, key=lambda orden: orden['ordenCompleto'])
    bloqueOrdenApi = [{b['nombre']: b['ordenCompleto']}
                      for b in ordenadosBloques]

    bloqueOrdenApi = [bloqueOrden for bloqueOrden in bloqueOrdenApi if list(bloqueOrden.values()) != [0]]

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

    '''SACA MAPEO SI ATRIBUTO ES TRUE'''
    listadoBloques = dict()
    listaMapeados = dict()
    bloquesInformacion = dict()

    '''Tendria que recuperar los bloques que estan como visibles'''
    bloquesInformacion['Articulos'] = listaArticulosDocente
    bloquesInformacion['Proyectos'] = proyectos
    bloquesInformacion['Capacitacion'] = Capacitacion
    bloquesInformacion['Libros'] = listaLibrosDocente
    bloquesInformacion['GradoAcademico'] = GradoAcademico

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

    listaResultados = []
    listaFinal = list()
    tituloBloque = dict()
    for i in bloquesRestantes:
        tituloBloque = i
        listaResultados.append(tituloBloque)
        for bloqueInformacion in bloquesInfoRestante[i]:
            resultados = dict(
                zip(bloqueInformacion['mapeo'], bloqueInformacion.values()))
            listaResultados.append(resultados)

        listaFinal.append(listaResultados)
        listaResultados = []
        tituloBloque = {}

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





'''GENERA PDF RESUMIDO'''
def JsonResumido(request, id):
    model_dict = models.ConfiguracionCv.objects.all().values()
    model_bloques = models.Bloque.objects.all().values()

    r = requests.get(f'https://sica.utpl.edu.ec/ws/api/docentes/{id}/',
                     headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'})
    docente = r.json()

    '''Saca id Articulos '''
    listaidArticulos = []
    for infobloque in docente['related']['articulos']:
        listaidArticulos.append(infobloque)

    idsArticulos = [fila['id'] for fila in listaidArticulos]

    '''Saca id Libros '''
    listaidLibros = []
    for infoLibros in docente['related']['libros']:
        listaidLibros.append(infoLibros)

    idsLibros = [fila['id'] for fila in listaidLibros]

    ''' Saca articulos de docentes por ID'''
    listaArticulosDocente = []
    for id in idsArticulos:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/articulos/' + str(id) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaArticulosDocente.append(todos)

    ''' Saca libros de docentes por ID'''
    listaLibrosDocente = []
    for idLibro in idsLibros:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/libros/' + str(idLibro) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaLibrosDocente.append(todos)

    '''Cambia valores None por cadena ('None') '''
    for i in listaLibrosDocente:
        for key, value in i.items():
            if value is None:
                value = 'None'
            i[key] = value

    proyectos = []
    Capacitacion = []
    GradoAcademico = []

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

    '''SACA MAPEO SI ATRIBUTO ES TRUE'''
    listadoBloques = dict()
    listaMapeados = dict()
    bloquesInformacion = dict()

    '''Tendria que recuperar los bloques que estan como visibles'''
    bloquesInformacion['Articulos'] = listaArticulosDocente
    bloquesInformacion['Proyectos'] = proyectos
    bloquesInformacion['Capacitacion'] = Capacitacion
    bloquesInformacion['Libros'] = listaLibrosDocente
    bloquesInformacion['GradoAcademico'] = GradoAcademico

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



def JsonPersonalizado(request, id, nombre_cv, cvHash):

    model_dict = models.ConfiguracionCv_Personalizado.objects.all().values()
    # print('model_dictPersonalizadolala', model_dict.filter(id_user=4).filter(nombre_cv = nombre_cv))
    dataFilterId = model_dict.filter(id_user=id)

    # print('model_ditct--------------____>>>>>>>>>>>>>>>>>>>>>>>', dataFilterId)
    # dataHash = dataFilterId.filter(cv=cvHash)
    # print('model_ditct--------------____>>>>>>>>>>>>>>>>>>>>>>>', dataHash)

    dataPersonalizada = dataFilterId.filter(nombre_cv=nombre_cv).filter(cv=cvHash)


    # print('DATAPERSONALIZADA--------------____>>>>>>>>>>>>>>>>>>>>>>>', dataPersonalizada)
    # print('NOMBRECV--------------____>>>>>>>>>>>>>>>>>>>>>>>', dataPersonalizada)

    # model_bloques = models.Bloque.objects.all().values()

    r = requests.get(f'https://sica.utpl.edu.ec/ws/api/docentes/{id}/',
                     headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'})
    docente = r.json()

    '''Saca id Articulos '''
    listaidArticulos = []
    for infobloque in docente['related']['articulos']:
        listaidArticulos.append(infobloque)

    idsArticulos = [fila['id'] for fila in listaidArticulos]

    '''Saca id Libros '''
    listaidLibros = []
    for infoLibros in docente['related']['libros']:
        listaidLibros.append(infoLibros)

    idsLibros = [fila['id'] for fila in listaidLibros]

    ''' Saca articulos de docentes por ID'''
    listaArticulosDocente = []
    for id in idsArticulos:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/articulos/' + str(id) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaArticulosDocente.append(todos)
    #   print('listaArticulosDocente------------>>>>>>>>>>>>>>>>>',listaArticulosDocente)

    ''' Saca libros de docentes por ID'''
    listaLibrosDocente = []
    for idLibro in idsLibros:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/libros/' + str(idLibro) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaLibrosDocente.append(todos)
        # print('listaArticulosDocente------------>>>>>>>>>>>>>>>>>',listaLibrosDocente)

    '''Cambia valores None por cadena ('None') '''
    for i in listaLibrosDocente:
        for key, value in i.items():
            if value is None:
                value = 'None'
            i[key] = value

    proyectos = []
    Capacitacion = []
    GradoAcademico = []

    '''BLOQUES DE MODEL BLOQUES ORDENADOS '''
    ordenadosBloquesAPi = sorted(
        dataPersonalizada, key=lambda orden: orden['ordenPersonalizable'])
    # print("ORDENADOSBLOQUESORIGINAL--------------->>>>>>>>>>>", ordenadosBloquesAPi)

    bloqueOrdenApi = [{b['nombreBloque']: b['visible_cv_bloque']}
                      for b in ordenadosBloquesAPi]

    # print("ORDENADOSBLOQUESORIGINALORDENAPI------->>>>>>>>>>>", bloqueOrdenApi)
    # ordenadosBloquesApi = sorted(bloqueOrdenApi, key=lambda orden: orden["ordenPersonalizable"])
    # print("ORDENADOSBLOQUESAPI------->>>>>>>>>>>", ordenadosBloquesApi)

    seen = set()
    bloquesOrdenados = []
    for d in bloqueOrdenApi:
        t = tuple(d.items())
        if t not in seen:
            seen.add(t)
            bloquesOrdenados.append(d)


    ordenadosBloques = [bloqueOrden for bloqueOrden in bloquesOrdenados if list(bloqueOrden.values()) != [False]]
    # print("ordenadosBloques------->>>>>>>>>>>", ordenadosBloques)

    listaBloques = [[x for x, v in i.items()] for i in ordenadosBloques]
    listaBloquesOrdenados = [y for x in listaBloques for y in x]
    # print("listaBloquesOrdenados------------_______>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", listaBloquesOrdenados)

    '''SACA VISIBLES SI SON TRUE'''
    diccionario = dict()
    for i in listaBloquesOrdenados:
        visibles = [{'nombre': d['atributo'], 'orden': d['orden']} for d in dataPersonalizada if d.get(
            "visible_cv_personalizado") and d.get('bloque') == i]
        ordenadosAtributos = sorted(visibles, key=lambda orden: orden['orden'])
        listaatrvisibles = [[valor for clave, valor in i.items(
        ) if clave == 'nombre'] for i in ordenadosAtributos]
        listaVisiblesAtr = [y for x in listaatrvisibles for y in x]
        # print('listaatrvisibles', listaVisiblesAtr, '\n')  

        diccionario[i] = listaVisiblesAtr

    '''SACA MAPEO SI ATRIBUTO ES TRUE'''
    listadoBloques = dict()
    listaMapeados = dict()
    bloquesInformacion = dict()

    '''Tendria que recuperar los bloques que estan como visibles'''
    bloquesInformacion['Articulos'] = listaArticulosDocente
    bloquesInformacion['Proyectos'] = proyectos
    bloquesInformacion['Capacitacion'] = Capacitacion
    bloquesInformacion['Libros'] = listaLibrosDocente
    bloquesInformacion['GradoAcademico'] = GradoAcademico

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
        # print('filtrados---___________>>>>>>>>>>>>>>>>>>>',i, filtrados)
        listadoBloques[i] = filtrados

    bloqueAtributos = dict()
    for listadoBloque in listadoBloques:
        bloqueAtributos[listadoBloque] = [{atributo: d.get(atributo) for atributo in diccionario[listadoBloque] if d.get(
            atributo) != None} for d in bloquesInformacion[listadoBloque]]
    # print('filtrados->>>>>>>>>>>>>>>>>>>>>>>', bloqueAtributos)

    bloquesInfoRestante = {k: v for k, v in bloqueAtributos.items() if [
        item for item in v if item != {}]}
    # print('bloquesInfoRestante', bloquesInfoRestante)

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



def GeneraTxtInformacion(request, id):
    r = requests.get(f'https://sica.utpl.edu.ec/ws/api/docentes/{id}/',
                     headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'})
    docente = r.json()

    print("DOCENTEBIBTEX", docente['primer_apellido'])

    
    '''Saca id Articulos '''
    listaidArticulos = []
    for infobloque in docente['related']['articulos']:
        listaidArticulos.append(infobloque)

    idsArticulos = [fila['id'] for fila in listaidArticulos]

    '''Saca id Libros '''
    listaidLibros = []
    for infoLibros in docente['related']['libros']:
        listaidLibros.append(infoLibros)

    idsLibros = [fila['id'] for fila in listaidLibros]

    ''' Saca articulos de docentes por ID'''
    listaArticulosDocente = []
    for id in idsArticulos:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/articulos/' + str(id) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaArticulosDocente.append(todos)

    ''' Saca libros de docentes por ID'''
    listaLibrosDocente = []
    for idLibro in idsLibros:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/libros/' + str(idLibro) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaLibrosDocente.append(todos)

    '''Cambia valores None por cadena ('None') '''
    for i in listaLibrosDocente:
        for key, value in i.items():
            if value is None:
                value = 'None'
            i[key] = value

    # proyectos = []
    # Capacitacion = []
    GradoAcademico = []

    proyectos = []

    Capacitacion = []

    response = BibDatabase()
    # print(response.entries)


    lines = []

    for libro in listaLibrosDocente:
        fecha = datetime.now()
        titulo = libro['titulo']
        revista = libro['editorial']
        link_libro = libro['link_descarga_1']
        isbn = libro['isbn']
        tipo_documento = libro['tipo_libro']
        ambito_editorial = libro['ambito_editorial']
        lines.append(f'LIBROS\nSIAC UTPL\nEXPORT DATE:{fecha}\n{titulo}\n{revista}\n{link_libro}\nISBN:{isbn}\nDOCUMENT TYPE:{tipo_documento}\nEDITORIAL SCOPE:{ambito_editorial}\nSOURCE:SIAC UTPL\n\n\n\n\n\n')


    
    for articulo in listaArticulosDocente:
        try:
            fecha = datetime.now()
            titulo = articulo['titulo']
            revista = articulo['revista']
            link_articulo = articulo['link_articulo']
            doi = articulo['doi']
            tipo_documento = articulo['tipo_documento']
            publication_stage = articulo['estado']
            lines.append(f'ARTICULOS\nSIAC UTPL\nEXPORT DATE:{fecha}\n{titulo}\n{revista}\n{link_articulo}\nDOI:{doi}\nDOCUMENT TYPE:{tipo_documento}\nPUBLICATION STAGE:{publication_stage}\nSOURCE:SIAC UTPL\n\n\n\n\n\n')
        except:
            print("asdsadsa")
        
    
   

    # lines = []
    for pryecto in proyectos:
        fecha = datetime.now()
        nombre_proyecto = pryecto['nombre_proyecto']
        fecha_inicio = pryecto['fecha_inicio']
        fecha_cierre = pryecto['fecha_cierre']
        tipo_proyecto = pryecto['tipo_proyecto']
        # tipo_documento = libro['tipo_libro']
        # ambito_editorial = libro['ambito_editorial']
        lines.append(f'PROYECTOS]\nSIAC UTPL\nEXPORT DATE:{fecha}\n{nombre_proyecto}\n{fecha_inicio}\n{fecha_cierre}\nTIPO PROYECTO:{tipo_proyecto}\nSOURCE:SIAC UTPL\n\n\n\n\n\n')



    for capacitacion in Capacitacion:
        fecha = datetime.now()
        nombre = capacitacion['nombre_proyecto']
        fecha_inicio = capacitacion['fecha_inicio']
        # fecha_fin = capacitacion['fecha_cierre']
        institucion_organizadora = capacitacion['institucion_organizadora']
        # tipo_documento = libro['tipo_libro']
        # ambito_editorial = libro['ambito_editorial']
        lines.append(f'CAPACITACIÓN\nSIAC UTPL\nEXPORT DATE:{fecha}\n{nombre}\n{fecha_inicio}\n{fecha_inicio}\nINSTITUCIÓN:{institucion_organizadora}\nSOURCE:SIAC UTPL\n\n\n\n\n\n')

    for gradoAcademico in GradoAcademico:
        fecha = datetime.now()
        nombre = gradoAcademico['denominacion_titulo']
        fecha_inicio = gradoAcademico['fecha_inicio']
        # fecha_fin = capacitacion['fecha_cierre']
        institucion_organizadora = gradoAcademico['universidad_emisora']
        # tipo_documento = libro['tipo_libro']
        # ambito_editorial = libro['ambito_editorial']
        lines.append(f'SIAC UTPL\nEXPORT DATE:{fecha}\n{nombre}\n{fecha_inicio}\n{fecha_inicio}\nINSTITUCIÓN:{institucion_organizadora}\nSOURCE:SIAC UTPL\n\n\n\n\n\n')


    print(lines)
    # response.entries = lines
    # writer = BibTexWriter()
    # data = writer.write(response)
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename=export.txt'
   
    response.writelines(lines)

    return response




'''GENERA PDF RESUMIDO'''
def InformacionTxtArticulos(request, id):

    r = requests.get(f'https://sica.utpl.edu.ec/ws/api/docentes/{id}/',
                     headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'})
    docente = r.json()

    '''Saca id Articulos '''
    listaidArticulos = []
    for infobloque in docente['related']['articulos']:
        listaidArticulos.append(infobloque)

    idsArticulos = [fila['id'] for fila in listaidArticulos]


    ''' Saca articulos de docentes por ID'''
    listaArticulosDocente = []
    for id in idsArticulos:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/articulos/' + str(id) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaArticulosDocente.append(todos)

    '''Cambia valores None por cadena ('None') '''
    for i in listaArticulosDocente:
        for key, value in i.items():
            if value is None:
                value = 'None'
            i[key] = value

    print("Articulos----->>>>>>>>>>>>>>>>>>>>>",listaArticulosDocente)

    lines = []
    for articulo in listaArticulosDocente:
        try:
            fecha = datetime.now()
            titulo = articulo['titulo']
            revista = articulo['revista']
            link_articulo = articulo['link_articulo']
            doi = articulo['doi']
            tipo_documento = articulo['tipo_documento']
            publication_stage = articulo['estado']
            lines.append(f'SIAC UTPL\nEXPORT DATE:{fecha}\n{titulo}\n{revista}\n{link_articulo}\nDOI:{doi}\nDOCUMENT TYPE:{tipo_documento}\nPUBLICATION STAGE:{publication_stage}\nSOURCE:SIAC UTPL\n\n\n\n\n\n')
        except:
            print("asdsadsa")

    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename=export.txt'
   
    response.writelines(lines)

    return response


def InformacionTxtLibros(request, id):

    r = requests.get(f'https://sica.utpl.edu.ec/ws/api/docentes/{id}/',
                     headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'})
    docente = r.json()

    '''Saca id Articulos '''
    listaidLibros = []
    for infobloque in docente['related']['libros']:
        listaidLibros.append(infobloque)

    idsLibros = [fila['id'] for fila in listaidLibros]


    ''' Saca articulos de docentes por ID'''
    listaLibrosDocente = []
    for id in idsLibros:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/libros/' + str(id) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaLibrosDocente.append(todos)

    '''Cambia valores None por cadena ('None') '''
    for i in listaLibrosDocente:
        for key, value in i.items():
            if value is None:
                value = 'None'
            i[key] = value


    lines = []
    arreglo = [{libro['titulo'], libro['editorial']} for libro in listaLibrosDocente]
    print("ARREGLO----------_______>>>>>>>>>>>>>.", arreglo)
    

    for libro in listaLibrosDocente:
        fecha = datetime.now()
        titulo = libro['titulo']
        revista = libro['editorial']
        link_libro = libro['link_descarga_1']
        isbn = libro['isbn']
        tipo_documento = libro['tipo_libro']
        ambito_editorial = libro['ambito_editorial']
        lines.append(f'SIAC UTPL\nEXPORT DATE:{fecha}\n{titulo}\n{revista}\n{link_libro}\nISBN:{isbn}\nDOCUMENT TYPE:{tipo_documento}\nEDITORIAL SCOPE:{ambito_editorial}\nSOURCE:SIAC UTPL\n\n\n\n\n\n')



    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename=export.txt'
   
    response.writelines(lines)

    return response



def InformacionTxtProyectos(request, id):

    r = requests.get(f'https://sica.utpl.edu.ec/ws/api/docentes/{id}/',
                     headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'})
    docente = r.json()

    '''Saca id Articulos '''
    listaidLibros = []
    for infobloque in docente['related']['proyectos']:
        listaidLibros.append(infobloque)

    idsLibros = [fila['id'] for fila in listaidLibros]


    ''' Saca articulos de docentes por ID'''
    listaLibrosDocente = []
    for id in idsLibros:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/proyectos/' + str(id) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaLibrosDocente.append(todos)

    '''Cambia valores None por cadena ('None') '''
    for i in listaLibrosDocente:
        for key, value in i.items():
            if value is None:
                value = 'None'
            i[key] = value


    lines = []
    # arreglo = [{libro['titulo'], libro['editorial']} for libro in listaLibrosDocente]
    # print("ARREGLO----------_______>>>>>>>>>>>>>.", arreglo)
    

    for pryecto in listaLibrosDocente:
        fecha = datetime.now()
        nombre_proyecto = pryecto['nombre_proyecto']
        fecha_inicio = pryecto['fecha_inicio']
        fecha_cierre = pryecto['fecha_cierre']
        tipo_proyecto = pryecto['tipo_proyecto']
        # tipo_documento = libro['tipo_libro']
        # ambito_editorial = libro['ambito_editorial']
        lines.append(f'SIAC UTPL\nEXPORT DATE:{fecha}\n{nombre_proyecto}\n{fecha_inicio}\n{fecha_cierre}\nTIPO PROYECTO:{tipo_proyecto}\nSOURCE:SIAC UTPL\n\n\n\n\n\n')


    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename=export.txt'
   
    response.writelines(lines)

    return response


def InformacionTxtCapacitacion(request, id):

    r = requests.get(f'https://sica.utpl.edu.ec/ws/api/docentes/{id}/',
                     headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'})
    docente = r.json()

    '''Saca id Articulos '''
    listaidLibros = []
    for infobloque in docente['related']['capacitacion']:
        listaidLibros.append(infobloque)

    idsLibros = [fila['id'] for fila in listaidLibros]


    ''' Saca articulos de docentes por ID'''
    listaLibrosDocente = []
    for id in idsLibros:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/capacitacion/' + str(id) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaLibrosDocente.append(todos)

    '''Cambia valores None por cadena ('None') '''
    for i in listaLibrosDocente:
        for key, value in i.items():
            if value is None:
                value = 'None'
            i[key] = value


    lines = []
    # arreglo = [{libro['titulo'], libro['editorial']} for libro in listaLibrosDocente]
    # print("ARREGLO----------_______>>>>>>>>>>>>>.", arreglo)
    

    for capacitacion in listaLibrosDocente:
        fecha = datetime.now()
        nombre = capacitacion['nombre_proyecto']
        fecha_inicio = capacitacion['fecha_inicio']
        # fecha_fin = capacitacion['fecha_cierre']
        institucion_organizadora = capacitacion['institucion_organizadora']
        # tipo_documento = libro['tipo_libro']
        # ambito_editorial = libro['ambito_editorial']
        lines.append(f'SIAC UTPL\nEXPORT DATE:{fecha}\n{nombre}\n{fecha_inicio}\n{fecha_inicio}\nINSTITUCIÓN:{institucion_organizadora}\nSOURCE:SIAC UTPL\n\n\n\n\n\n')


    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename=export.txt'
   
    response.writelines(lines)

    return response


def InformacionTxtGradoAcademico(request, id):

    r = requests.get(f'https://sica.utpl.edu.ec/ws/api/docentes/{id}/',
                     headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'})
    docente = r.json()

    '''Saca id Articulos '''
    listaidLibros = []
    for infobloque in docente['related']['grado-academico']:
        listaidLibros.append(infobloque)

    idsLibros = [fila['id'] for fila in listaidLibros]


    ''' Saca articulos de docentes por ID'''
    listaLibrosDocente = []
    for id in idsLibros:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/grado-academico/' + str(id) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaLibrosDocente.append(todos)

    '''Cambia valores None por cadena ('None') '''
    for i in listaLibrosDocente:
        for key, value in i.items():
            if value is None:
                value = 'None'
            i[key] = value


    lines = []
    # arreglo = [{libro['titulo'], libro['editorial']} for libro in listaLibrosDocente]
    # print("ARREGLO----------_______>>>>>>>>>>>>>.", arreglo)
    

    for gradoAcademico in listaLibrosDocente:
        fecha = datetime.now()
        nombre = gradoAcademico['denominacion_titulo']
        fecha_inicio = gradoAcademico['fecha_inicio']
        # fecha_fin = capacitacion['fecha_cierre']
        institucion_organizadora = gradoAcademico['universidad_emisora']
        # tipo_documento = libro['tipo_libro']
        # ambito_editorial = libro['ambito_editorial']
        lines.append(f'SIAC UTPL\nEXPORT DATE:{fecha}\n{nombre}\n{fecha_inicio}\n{fecha_inicio}\nINSTITUCIÓN:{institucion_organizadora}\nSOURCE:SIAC UTPL\n\n\n\n\n\n')


    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename=export.txt'
   
    response.writelines(lines)

    return response



''''GENERA CSV COMPLETO'''
def InformacionCsv(request, id):
    # Create the HttpResponse object with the appropriate CSV header.
    model_dict = models.ConfiguracionCv.objects.all().values()
    model_bloques = models.Bloque.objects.all().values()

    r = requests.get(f'https://sica.utpl.edu.ec/ws/api/docentes/{id}/',
                     headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'})
    docente = r.json()

    '''Saca id Articulos '''
    listaidArticulos = []
    for infobloque in docente['related']['articulos']:
        listaidArticulos.append(infobloque)

    idsArticulos = [fila['id'] for fila in listaidArticulos]

    '''Saca id Libros '''
    listaidLibros = []
    for infoLibros in docente['related']['libros']:
        listaidLibros.append(infoLibros)

    idsLibros = [fila['id'] for fila in listaidLibros]

    ''' Saca articulos de docentes por ID'''
    listaArticulosDocente = []
    for id in idsArticulos:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/articulos/' + str(id) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaArticulosDocente.append(todos)
    #   print('listaArticulosDocente------------>>>>>>>>>>>>>>>>>',listaArticulosDocente)

    ''' Saca libros de docentes por ID'''
    listaLibrosDocente = []
    for idLibro in idsLibros:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/libros/' + str(idLibro) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaLibrosDocente.append(todos)
        print('listaArticulosDocente------------>>>>>>>>>>>>>>>>>',listaLibrosDocente)

    '''Cambia valores None por cadena ('None') '''
    for i in listaLibrosDocente:
        for key, value in i.items():
            if value is None:
                value = 'None'
            i[key] = value

    proyectos = []
    Capacitacion = []
    GradoAcademico = []

    '''BLOQUES DE MODEL BLOQUES ORDENADOS '''
    ordenadosBloques = sorted(
        model_bloques, key=lambda orden: orden['ordenCompleto'])
    bloqueOrdenApi = [{b['nombre']: b['ordenCompleto']}
                      for b in ordenadosBloques]

    bloqueOrdenApi = [bloqueOrden for bloqueOrden in bloqueOrdenApi if list(bloqueOrden.values()) != [0]]


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

    '''SACA MAPEO SI ATRIBUTO ES TRUE'''
    listadoBloques = dict()
    listaMapeados = dict()
    bloquesInformacion = dict()

    '''Tendria que recuperar los bloques que estan como visibles'''
    bloquesInformacion['Articulos'] = listaArticulosDocente
    bloquesInformacion['Proyectos'] = proyectos
    bloquesInformacion['Capacitacion'] = Capacitacion
    bloquesInformacion['Libros'] = listaLibrosDocente
    bloquesInformacion['GradoAcademico'] = GradoAcademico

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
   
    listaResultados = []
    listaFinal = list()
    tituloBloque = dict()
    
    for i in bloquesRestantes:
        tituloBloque[''] = i.upper()
        listaResultados.append(tituloBloque)
        for bloqueInformacion in bloquesInfoRestante[i]:
            resultados = dict(
                zip(bloqueInformacion['mapeo'], bloqueInformacion.values()))
            listaResultados.append(resultados)

        listaFinal.append(listaResultados)
        listaResultados = []
        tituloBloque = {}

    response = HttpResponse(content_type='text/csv')  
    response['Content-Disposition'] = 'attachment; filename="file.csv"'  
    writer = csv.writer(response)  
    
    for lista in listaFinal:
        # print(lista)
        for i in lista:
            writer.writerow(f'{k}' for k, v in i.items()) 
            writer.writerow(v for k, v in i.items())


    return response  



def generaBibTex(request, id):

    r = requests.get(f'https://sica.utpl.edu.ec/ws/api/docentes/{id}/',
                     headers={'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'})
    docente = r.json()

    print("DOCENTEBIBTEX", docente['primer_apellido'])

    
    '''Saca id Articulos '''
    listaidArticulos = []
    for infobloque in docente['related']['articulos']:
        listaidArticulos.append(infobloque)

    idsArticulos = [fila['id'] for fila in listaidArticulos]

    '''Saca id Libros '''
    listaidLibros = []
    for infoLibros in docente['related']['libros']:
        listaidLibros.append(infoLibros)

    idsLibros = [fila['id'] for fila in listaidLibros]

    ''' Saca articulos de docentes por ID'''
    listaArticulosDocente = []
    for id in idsArticulos:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/articulos/' + str(id) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaArticulosDocente.append(todos)

    ''' Saca libros de docentes por ID'''
    listaLibrosDocente = []
    for idLibro in idsLibros:
        r = requests.get('https://sica.utpl.edu.ec/ws/api/libros/' + str(idLibro) + "/",
                         headers={
                             'Authorization': 'Token 54fc0dc20849860f256622e78f6868d7a04fbd30'}
                         )
        todos = r.json()
        listaLibrosDocente.append(todos)

    '''Cambia valores None por cadena ('None') '''
    for i in listaLibrosDocente:
        for key, value in i.items():
            if value is None:
                value = 'None'
            i[key] = value

    # proyectos = []
    # Capacitacion = []
    GradoAcademico = []

    proyectos = []

    Capacitacion = []

    response = BibDatabase()
    # print(response.entries)


    lines = []

    for libro in listaLibrosDocente:
        const = {
          'editorial ': libro['editorial'],
          'comments' : "asdsa",
          'abstract' : 'description test',
          'title   ' : libro['titulo'],
          'year    ' : str(libro['anio']),
          'volume  ' : '1',
          'ID' : "Marco Vinicio",
          'ENTRYTYPE': 'book'
        }
        lines.append(const)

    
    for articulo in listaArticulosDocente:
        # print('REVIST-_____>>>>>>>>>>>>>>>>>>>>>', articulo['volume'])
        try:
            const = {
              'journal ': articulo['revista'],
            #   'comments' : articulo['abstract'],
              'abstract' : articulo['abstract'],
              'title   ' : articulo['titulo'],
              'year    ' : str(articulo['year']),
              'volume  ' : str(articulo['volume']),
              'ID' : docente['primer_apellido'] + str(articulo['year']),
              'keywords': articulo["keywords"],
              'ENTRYTYPE': 'article'
            }
            lines.append(const)
        except:
            print("asdassa")
        
    
   

    # lines = []
    for proyecto in proyectos:
      const = {
          'journal ': proyecto['descripcion'],
          'comments' : proyecto['descripcion'],
          'abstract' : proyecto['descripcion'],
          'title   ' : proyecto['nombre_proyecto'],
          'year    ' : str(proyecto['fecha_cierre']),
          'volume  ' : '1',
          'ID' : docente['primer_apellido'],
          'ENTRYTYPE': 'proyect'
      }
      lines.append(const)

    for capacitacion in Capacitacion:
      print("CAPACITACION", capacitacion)
      const = {
          'journal ': capacitacion['tematica'],
          'comments' : capacitacion['comite_organizador'],
          'abstract' : capacitacion['comite_organizador'],
          'title   ' : capacitacion['nombre'],
          'date    ' : capacitacion['fecha_fin'],
          'volume  ' : '1',
          'ID' : "Marco Vinicio",
          'ENTRYTYPE': 'capacitation'
      }
      lines.append(const)

    print(lines)
    response.entries = lines
    writer = BibTexWriter()
    data = writer.write(response)

    # with open('bibtex.bib', 'w') as bibfile:
    #     bibfile.write(writer.write(db))
    print("BIBFILE-------__>>>>>>>>", writer.write(response))
    
    response = HttpResponse(data, content_type='text/x-bibtex')  
    response['Content-Disposition'] = 'attachment; filename="file.bib"' 

    return response