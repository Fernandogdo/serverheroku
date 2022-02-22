from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework import exceptions

from .models import *

class PatchModelSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        kwargs['partial'] = True
        super(PatchModelSerializer, self).__init__(*args, **kwargs)


class ConfiguracionCvSerializer(serializers.ModelSerializer):

    class Meta:
        model = ConfiguracionCv
        fields = '__all__'


class UsuarioSerializer(serializers.ModelSerializer):

    class Meta:
        model = Usuario()
        fields = ('id_user', 'is_staff', 'username', 'first_name', 'last_name', 'password')
    def save(self):
        user = Usuario(
                    id_user=self.validated_data['id_user'],
                    username=self.validated_data['username'],
                    first_name=self.validated_data['first_name'],
                    last_name=self.validated_data['last_name'],
            )
        password = self.validated_data['password']
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        username = data.get("username", "")
        password = data.get("password", "")

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    data["user"] = user
                else:
                    raise exceptions.ValidationError("Usuario esta desactivado")
            else:
                raise exceptions.ValidationError("Los datos son incorrectos")
        else:
            raise exceptions.ValidationError("No se deben dejar campos sin llenar")
        return data


class ConfiguracionCv_PersonalizadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfiguracionCv_Personalizado
        fields = '__all__'
        

class BloqueSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Bloque
        fields = ('__all__')


class ServicioSerializer(serializers.ModelSerializer):

    class Meta:
        model = Servicio
        fields = ('__all__')