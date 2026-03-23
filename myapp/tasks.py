from celery import shared_task
from django.db import connections
import pandas as pd

@shared_task
def obtener_y_procesar_datos():
    conexion_ct = connections['control_total']
    with conexion_ct.cursor() as cursor:
        parametros = ("1/11/2023", "2/11/2023", 0, 0)
        cursor.callproc('DAC_REPORTE_VENTAS_GENERAL', parametros)
        datos = cursor.fetchall()
        dataframe = pd.DataFrame(datos, columns=[col[0] for col in cursor.description])

    return dataframe
