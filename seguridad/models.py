from django.db import models

class Permiso(models.Model):
    posicionMenu = models.CharField(max_length=100)
    tiene_acceso = models.BooleanField(default=True)
    class Meta:
        app_label = 'seguridad'
    

class Usuario(models.Model):
    nombre = models.CharField(max_length=50, default='', blank=False)
    apellido = models.CharField(max_length=30, null=True, blank=True)
    usuario = models.CharField(max_length=20, blank=False)
    contrasena = models.CharField(max_length=50, null=True, blank=True)
    estado = models.IntegerField(default=1, help_text='1 ACTIVO| 2 RETIRADO')
    fecha = models.DateTimeField(auto_now_add=True)
    is_built_in = models.BooleanField(default=False)
    descuento = models.DecimalField(max_digits=9, decimal_places=2, default=0.00)
    pass_requerido = models.IntegerField(default=0)
    ventas = models.BooleanField(default=False)
    comisiones = models.BooleanField(default=False)
    fk_puesto = models.IntegerField(default=0)
    correo = models.CharField(max_length=100, default=' ')
    id_telegram = models.CharField(max_length=30, default=' ', help_text='-880470424 <----- ESTE ID TELEGRAM ES GENERAL PARA EVITAR ERRORES CON EL API DEL BOT AL MOMENTO DE NO ENCONTRAR UN ID TELEGRAM')
    identidad = models.CharField(max_length=20, default=' ')
    telefono = models.CharField(max_length=20, default=' ')
    direccion = models.TextField(null=True, blank=True)
    fk_cargo = models.IntegerField(default=0)

    class Meta:
        db_table = 'usuarios'
        app_label = 'seguridad'

