# Generated by Django 3.1.7 on 2022-02-21 21:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cv_api', '0008_remove_configuracioncv_bloqueservice'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuracioncv',
            name='bloqueService',
            field=models.CharField(default='articulos', max_length=150),
        ),
    ]