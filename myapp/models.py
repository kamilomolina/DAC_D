from django.db import models

class Telefonos(models.Model):
    codigo_verificacion = models.IntegerField(blank=True, null=True)
    registrado = models.BooleanField(default=False)
    nombre_empleado = models.CharField(max_length=255, blank=True, null=True)
    mac_address = models.CharField(max_length=255, blank=True, null=True)
    imei_1 = models.CharField(max_length=255, blank=True, null=True, db_column='IMEI 1')
    id_telegram = models.CharField(max_length=255, blank=True, null=True)
    numero_telefono = models.CharField(max_length=255, blank=True, null=True)
    activo = models.BooleanField(default=False)
    observaciones = models.CharField(max_length=255, blank=True, null=True)
    id_vendedor = models.IntegerField(default=1)
    id_supervisor = models.IntegerField(default=1)
    venta_pma = models.BooleanField(default=False)
    venta_carbajal = models.BooleanField(default=False)
    acceso_total = models.BooleanField(default=True)
    usuario = models.CharField(max_length=255, null=True, default=None)
    perfil_empleado = models.IntegerField(null=True, default=None)

    class Meta:
        #Así se llama la tabla de los telefonos en la base de pedidos.
        db_table = 'telefonos'

    def __str__(self):
        return self.nombre_empleado or 'Telefono sin nombre'

class Supervisor(models.Model):
    nombre = models.CharField(max_length=255)
    id_telegram = models.CharField(max_length=15, blank=True, null=True)
    es_jefe = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    id_supervisor = models.IntegerField(default=0)
    porcentaje = models.DecimalField(max_digits=12, decimal_places=1, default=0.0)
    it = models.BooleanField(blank=True, null=True)
    es_supervisor = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table= 'supervisor'
        unique_together = (('id',),)


class Vendedor(models.Model):
    id_vendedor = models.AutoField(primary_key=True)
    codigo_vendedor = models.IntegerField(null=True, blank=True)
    nombre_vendedor = models.CharField(max_length=25, null=True, blank=True)
    id_sucursal = models.IntegerField(null=True, blank=True)
    id_supervisor = models.IntegerField(null=True, blank=True)
    activo = models.BooleanField(null=True, blank=True)

    class Meta:
        db_table = 'vendedores'


from django.db import models

class MgRuta(models.Model):
    id_ruta = models.AutoField(primary_key=True)
    ruta = models.CharField(max_length=255, blank=True, null=True)
    nombre_vendedor = models.CharField(max_length=255, blank=True, null=True)
    activo = models.BooleanField(blank=True, null=True) 
    codigo_vendedor = models.IntegerField(blank=True, null=True)
    id_supervisor = models.IntegerField(blank=True, null=True)
    codigo_supervisor = models.IntegerField(blank=True, null=True)
    nombre_supervisor = models.CharField(max_length=255, blank=True, null=True)
    id_canal = models.IntegerField(blank=True, null=True)
    canal = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'mg_rutas'

class TelefonoAccesoRuta(models.Model):
    nombre_empleado = models.CharField(max_length=255, blank=True, null=True)
    codigo_verificacion = models.IntegerField(blank=True, null=True)
    mac_address = models.CharField(max_length=255, blank=True, null=True)
    observaciones = models.CharField(max_length=255, blank=True, null=True)
    codigo_vendedor = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    registrado_por = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'telefonos_accesosrutas'
