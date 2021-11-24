from django.db import models
from django.contrib.auth.models import AbstractBaseUser, AbstractUser
# Create your models here.
# from django_mysql.models import ListCharField


class Administrador(models.Model):
    idAministrador = models.AutoField(primary_key=True)

    class Meta:
        db_table = 'administrador'

class ConfiguracionCv(models.Model):
    id = models.AutoField(primary_key=True)
    administrador = models.ForeignKey(
        Administrador, related_name='Administrador', on_delete=models.CASCADE)
    bloque = models.CharField(max_length=150)
    atributo = models.CharField(max_length=100)
    ordenCompleto = models.IntegerField(default=1)
    ordenResumido = models.IntegerField(default=1)
    visible_cv_resumido = models.BooleanField(default=True)
    visible_cv_completo = models.BooleanField(default=True)
    mapeo = models.CharField(max_length=150, null=True, blank=True)

    # unique_together = ["bloque", "atributo"] 

    class Meta:
        unique_together = ["bloque", "atributo"] 
        db_table = 'configuracionCV'
        
class Docente(AbstractUser):

    id_user = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100, default="testname")
    last_name = models.CharField(max_length=100, default="test_lastname")
    username = models.CharField(max_length=100, unique=True, default="username")
    # password =  models.CharField(max_length=50)

    USERNAME_FIELD = 'username'

    REQUIRED_FIELDS = ['id_user', 'first_name', 'last_name']
    class Meta:
        db_table = 'docente'

class ConfiguracionCv_Personalizado(models.Model):
    id = models.AutoField(primary_key=True)
    # configuracionId = models.IntegerField()
    # id_atributo = models.IntegerField(default=1)
    id_user = models.ForeignKey(Docente, related_name='Docente',  on_delete=models.CASCADE)
    bloque = models.CharField(max_length=150)
    atributo = models.CharField(max_length=100)
    orden = models.IntegerField(default=1)
    # ordenResumido = models.IntegerField(default=1)
    visible_cv_personalizado = models.BooleanField(default=True)
    mapeo = models.CharField(max_length=150, blank=True)
    cv = models.CharField(max_length=20)
    nombre_cv = models.CharField(max_length=100, default="personalizado_cv")
    fecha_registro = models.DateTimeField(null=True, blank=True)
    cedula = models.TextField(max_length=11)
    nombreBloque = models.CharField(max_length=20, default="Articulos")
    ordenPersonalizable = models.IntegerField(default=1)
    visible_cv_bloque = models.BooleanField(default=True)
    class Meta:
        unique_together = ["bloque", "atributo", "nombre_cv", "cedula", "cv"] 
        db_table = 'configuracioncvPersonalizado'

        
                
class Bloque(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    ordenCompleto = models.IntegerField(default=1 )
    ordenResumido = models.IntegerField(default=0)
    ordenPersonalizable = models.IntegerField(default=0)
    visible_cv_bloqueCompleto = models.BooleanField(default=True)
    visible_cv_bloqueResumido = models.BooleanField(default=True)
    class Meta:
        db_table = 'bloque'

