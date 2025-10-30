from django.utils import timezone
from django.db import models

class DistribucionVehiculos(models.Model):
    id_vehiculo = models.AutoField(primary_key=True)
    nombre_vehiculo = models.CharField(max_length=255)
    capacidad_lbs = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    placa = models.CharField(max_length=25)
    id_empresa = models.IntegerField()
    id_tipo_vehiculo = models.IntegerField(default=0)
    disponibilidad = models.IntegerField(default=0, help_text='0 DISPONIBLE | 1 EN RUTA')
    estado = models.IntegerField(default=1, help_text='1 CREADO | 2 MODIFICADO | 3 ANULADO')
    creado_por = models.CharField(max_length=25)
    fecha_hora_creado = models.DateTimeField(default=timezone.now)
    modificado_por = models.CharField(max_length=25)
    fecha_hora_modificado = models.DateTimeField(null=True, blank=True)
    rendimiento_km = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    rendimiento_galon = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    id_combustible = models.IntegerField()

    class Meta:
        app_label = 'dac'
        db_table = 'distribucion_vehiculos'

    def save(self, *args, **kwargs):
        if self.id_combustible:  # Si el objeto ya existe (no es una creación nueva), actualiza la fecha de modificación
            self.fecha_hora_modificado = timezone.now()
        super().save(*args, using='dac', **kwargs)

from django.db import models

class DistribucionCombustibles(models.Model):
    id_combustible = models.AutoField(primary_key=True)
    nombre_combustible = models.CharField(max_length=255)
    precio_galon = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.IntegerField(default=1, help_text='1 CREADO | 2 MODIFICADO | 3 ANULADO')
    creado_por = models.CharField(max_length=25)
    fecha_hora_creado = models.DateTimeField(default=timezone.now)
    modificado_por = models.CharField(max_length=25)
    fecha_hora_modificado = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.nombre_combustible

    def save(self, *args, **kwargs):
        if self.id_combustible:  # Si el objeto ya existe (no es una creación nueva), actualiza la fecha de modificación
            self.fecha_hora_modificado = timezone.now()
        super().save(*args, using='dac', **kwargs)

    class Meta:
        app_label = 'dac'
        db_table = 'distribucion_combustibles'

class DistribucionDestinos(models.Model):
    id_destino = models.AutoField(primary_key=True)
    nombre_destino = models.CharField(max_length=255)
    descripcion_destino = models.TextField()
    distancia_km = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.IntegerField(default=1, help_text='1 CREADO | 2 MODIFICADO | 3 ANULADO')
    creado_por = models.CharField(max_length=25)
    fecha_hora_creado = models.DateTimeField(default=timezone.now)
    modificado_por = models.CharField(max_length=25)
    fecha_hora_modificado = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'dac'
        db_table = 'distribucion_destinos'  # Especifica el nombre de la tabla si es diferente al nombre del modelo

    def save(self, *args, **kwargs):
        # Actualiza fecha_hora_modificado solo si el registro ya existe
        if self.id_destino:
            self.fecha_hora_modificado = timezone.now()
        super().save(*args, **kwargs)

class DistribucionProgramacionDetalle(models.Model):
    id_programacion_detalle = models.AutoField(primary_key=True)
    id_programacion = models.IntegerField(null=True, blank=True)
    id_consolidado = models.IntegerField(null=True, blank=True)
    estado = models.IntegerField(null=True, blank=True)
    creado_por = models.CharField(max_length=25, null=True, blank=True)
    fecha_hora_creado = models.DateTimeField(null=True, blank=True)
    modificado_por = models.CharField(max_length=25, null=True, blank=True)
    fecha_hora_creacion = models.DateTimeField(default=timezone.now)

    class Meta:
        app_label = 'dac'
        db_table = 'distribucion_programacion_detalle'

    def save(self, *args, **kwargs):
        # Actualiza fecha_hora_modificado solo si el registro ya existe
        if self.id_programacion_detalle:
            self.fecha_hora_modificado = timezone.now()
        super().save(*args, **kwargs)

class DistribucionProgramacion(models.Model):
    id_programacion = models.AutoField(primary_key=True)
    fecha = models.DateTimeField()
    id_vehiculo = models.IntegerField()
    utilidad_operativa = models.DecimalField(max_digits=12, decimal_places=2)
    utilidad_total = models.DecimalField(max_digits=12, decimal_places=2)
    volumen = models.DecimalField(max_digits=12, decimal_places=2)
    peso_total = models.DecimalField(max_digits=12, decimal_places=2)
    cantidad_facturas = models.DecimalField(max_digits=12, decimal_places=2)
    cantidad_clientes = models.DecimalField(max_digits=12, decimal_places=2)
    rentabilidad = models.DecimalField(max_digits=12, decimal_places=2)
    cantidad_productos = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.IntegerField(null=True, blank=True)
    creado_por = models.CharField(max_length=25, null=True, blank=True)
    fecha_hora_creado = models.DateTimeField(null=True, blank=True)
    modificado_por = models.CharField(max_length=25, null=True, blank=True)
    fecha_hora_modificado = models.DateTimeField(default=timezone.now)

    class Meta:
        app_label = 'dac'
        db_table = 'distribucion_programacion'
    
    def save(self, *args, **kwargs):
        # Actualiza fecha_hora_modificado solo si el registro ya existe
        if self.id_programacion:
            self.fecha_hora_modificado = timezone.now()
        super().save(*args, **kwargs)


class DistribucionProgramacionHistorial(models.Model):
    id_programacion_historial = models.AutoField(primary_key=True)
    id_programacion = models.IntegerField(null=True, blank=True)
    hora_carga_inicio = models.DateTimeField(null=True, blank=True)
    hora_carga_fin = models.DateTimeField(null=True, blank=True)
    hora_entrega = models.DateTimeField(null=True, blank=True)
    hora_regreso = models.DateTimeField(null=True, blank=True)
    hora_fecha_esperado = models.DateTimeField(null=True, blank=True)
    usuario_carga_inicio = models.CharField(max_length=25, null=True, default=None)
    usuario_carga_fin = models.CharField(max_length=25, null=True, default=None)
    usuario_entrega = models.CharField(max_length=25, null=True, default=None)
    usuario_esperado = models.CharField(max_length=25, null=True, default=None)
    usuario_regreso = models.CharField(max_length=25, null=True, default=None)
    estado = models.IntegerField(null=True, blank=True)
    creado_por = models.CharField(max_length=25, null=True, blank=True)
    hora_fecha_creacion = models.DateTimeField(null=True, blank=True)
    modificado_por = models.CharField(max_length=25, null=True, blank=True)
    hora_fecha_modificacion = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'dac'
        db_table = 'distribucion_programacion_historial'

    def save(self, *args, **kwargs):
        # Actualiza fecha_hora_modificado solo si el registro ya existe
        if self.id_programacion_historial:
            self.fecha_hora_modificado = timezone.now()
        super().save(*args, **kwargs)


class DistribucionTripulantes(models.Model):
    id_tripulante = models.AutoField(primary_key=True)
    identidad_tripulante = models.CharField(max_length=255)
    nombre_tripulante = models.CharField(max_length=255)
    numero_licencia = models.CharField(max_length=255, null=True, blank=True)
    id_tipo_tripulante = models.IntegerField()
    disponibilidad = models.IntegerField(default=0, help_text='0 DISPONIBLE | 1 EN RUTA')
    estado = models.IntegerField(default=1, help_text='1 CREADO | 2 MODIFICADO | 3 ANULADO')
    creado_por = models.CharField(max_length=25)
    fecha_hora_creado = models.DateTimeField(default=timezone.now)
    licencia_vencimiento = models.DateField()
    modificado_por = models.CharField(max_length=25)
    fecha_hora_modificado = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'dac'
        db_table = 'distribucion_tripulantes'

    def __str__(self):
        return self.nombre_tripulante

    def save(self, *args, **kwargs):
        # Actualiza fecha_hora_modificado solo si el registro ya existe
        if self.id_tripulante:
            self.fecha_hora_modificado = timezone.now()
        super().save(*args, **kwargs)

class DistribucionTripulantesDetalleFlete(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    id_tripulante = models.IntegerField()  # Assuming this is a foreign key, you may want to use models.ForeignKey instead
    detalle_flete = models.TextField()
    valor_flete = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.IntegerField(default=1)
    creado_por = models.CharField(max_length=25)
    fecha_hora_creado = models.DateTimeField(auto_now_add=True)
    modificado_por = models.CharField(max_length=25)
    fecha_hora_modificado = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'dac'
        db_table = 'distribucion_tripulantes_detalle_flete'

    def save(self, *args, **kwargs):
        # Actualiza fecha_hora_modificado solo si el registro ya existe
        if self.id_tripulante:
            self.fecha_hora_modificado = timezone.now()
        super().save(*args, **kwargs)    


class DistribucionVehiculosDetalleFlete(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    id_vehiculo = models.IntegerField()  # Considera usar models.ForeignKey si es una relación con otra tabla
    detalle_flete = models.TextField()
    valor_flete = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.IntegerField(default=1)
    creado_por = models.CharField(max_length=25)
    fecha_hora_creado = models.DateTimeField(auto_now_add=True)
    modificado_por = models.CharField(max_length=25)
    fecha_hora_modificado = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'dac'
        db_table = 'distribucion_vehiculos_detalle_flete'

class DistribucionDestinosDetalleFlete(models.Model):
    id_detalle = models.AutoField(primary_key=True)
    id_destino = models.IntegerField()  # Considera usar models.ForeignKey si es una relación con otra tabla
    detalle_flete = models.TextField()
    valor_flete = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.IntegerField(default=1)
    creado_por = models.CharField(max_length=25)
    fecha_hora_creado = models.DateTimeField(auto_now_add=True)
    modificado_por = models.CharField(max_length=25)
    fecha_hora_modificado = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'dac'
        db_table = 'distribucion_destinos_detalle_flete'


class DistribucionProgramacionDestino(models.Model):
    id_programacion_destino = models.AutoField(primary_key=True)
    id_programacion = models.CharField(max_length=255, blank=True, null=True)
    id_destino = models.CharField(max_length=255, blank=True, null=True)
    estado = models.IntegerField(default=1, help_text='1 CREADO - 2 MODIFICADO - ELIMINADO')
    creado_por = models.CharField(max_length=25, blank=True, null=True)
    fecha_hora_creado = models.DateTimeField(blank=True, null=True)
    modificado_por = models.CharField(max_length=25, blank=True, null=True)
    fecha_hora_modificado = models.DateTimeField(blank=True, null=True)

    class Meta:
        app_label = 'dac'
        db_table = 'distribucion_programacion_destino'

class DistribucionProgramacionTripulantes(models.Model):
    id_programacion_tripulante = models.AutoField(primary_key=True)
    id_tripulante = models.CharField(max_length=255, blank=True, null=True)
    id_programacion = models.CharField(max_length=255, blank=True, null=True)
    estado = models.IntegerField(blank=True, null=True)
    creado_por = models.CharField(max_length=25, blank=True, null=True)
    fecha_hora_creado = models.DateTimeField(blank=True, null=True)
    modificado_por = models.CharField(max_length=25, blank=True, null=True)
    fecha_hora_modificado = models.DateTimeField(blank=True, null=True)

    class Meta:
        app_label = 'dac'
        db_table = 'distribucion_programacion_tripulantes'
