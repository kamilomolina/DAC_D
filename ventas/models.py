from django.db import models

class EmpresasCompetencias(models.Model):
    id_competencia = models.AutoField(primary_key=True)
    nombre_competencia = models.CharField(max_length=100, null=True, blank=True)
    descripcion = models.CharField(max_length=255, null= True, blank= True)
    estado = models.IntegerField(null=True, blank=True)
    creado_por = models.CharField(max_length=25, null=True, blank=True)
    fecha_hora_creado = models.DateTimeField(null=True, blank=True)
    modificado_por = models.CharField(max_length=25, null=True, blank=True)
    fecha_hora_modificado = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'dac'
        db_table = 'empresas_competencias'

class VentasPerdidasMotivos(models.Model):
    id_motivo = models.AutoField(primary_key=True)
    nombre_motivo = models.CharField(max_length=100, null=True, blank=True)
    descripcion_motivo = models.CharField(max_length=255, null=True, blank=True)
    tipo = models.IntegerField(null=True, blank=True)
    estado = models.IntegerField(null=True, blank=True)
    creado_por = models.CharField(max_length=25, null=True, blank=True)
    fecha_hora_creado = models.DateTimeField(null=True, blank=True)
    modificado_por = models.CharField(max_length=25, null=True, blank=True)
    fecha_hora_modificado = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'dac'
        db_table = 'ventas_perdidas_motivos'

class VentaPerdida(models.Model):
    id_venta_perdida = models.AutoField(primary_key=True)
    id_equivalencia_x_categoria = models.IntegerField(blank=True, null=True)
    nombre_producto = models.CharField(max_length=100, blank=True, null=True)
    id_pedido = models.IntegerField(blank=True, null=True)
    id_cliente = models.IntegerField(blank=True, null=True)
    nombre_cliente = models.CharField(max_length=100, blank=True, null=True)
    precio = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    precio_min = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    id_motivo = models.IntegerField(blank=True, null=True)
    id_competencia = models.IntegerField(blank=True, null=True)
    nombre_competencia = models.CharField(max_length=100, blank=True, null=True)
    comentario = models.CharField(max_length=255, blank=True, null=True)
    fecha = models.DateField(blank=True, null=True)
    estado = models.IntegerField(blank=True, null=True)
    creado_por = models.CharField(max_length=25, blank=True, null=True)
    fecha_hora_creacion = models.DateTimeField(blank=True, null=True)
    modificado_por = models.CharField(max_length=25, blank=True, null=True)
    fecha_hora_modificacion = models.DateTimeField(blank=True, null=True)
    cantidad = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    id_ruta = models.IntegerField(blank=True, null=True)
    nombre_ruta = models.CharField(max_length=100, blank=True, null=True)
    precio_competencia = models.CharField(max_length=255, blank=True, null=True)
    id_empresa = models.IntegerField(blank=True, null=True)
    presentacion = models.CharField(max_length=100, blank=True, null=True)
    grupo = models.CharField(max_length=150, null=True, blank=True)
    subgrupo = models.CharField(max_length=150, null=True, blank=True)
    categoria = models.CharField(max_length=150, null=True, blank=True)
    marca = models.CharField(max_length=150, null=True, blank=True)
    class Meta:
        app_label = 'dac'
        db_table = 'ventas_perdidas'
