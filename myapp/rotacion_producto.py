from decimal import Decimal
from django.db import connections
import pandas as pd
from pandas.tseries.offsets import MonthEnd
import numpy as np

class RotacionProducto:
    def __init__(self, mes, anio):
        self.mes = int(mes)
        self.anio = int(anio)
        self.conexion_ct = connections['control_total_test']
        self.conexion_ct2 = connections['control_total']
        self.resultados = pd.DataFrame()
        self.dataframe2 = pd.DataFrame()

    def obtener_datos_sp(self, conexion, nombre_sp):
        with conexion.cursor() as cursor:
            cursor.callproc(nombre_sp)
            columns = [col[0] for col in cursor.description]
            datos = cursor.fetchall()
            return pd.DataFrame(datos, columns=columns) if datos else pd.DataFrame()

    def cargar_datos(self):
        self.dataframe1 = self.obtener_datos_sp(self.conexion_ct, 'SP_DAC_D_GET_HISTORIAL_ROTACION')
        self.dataframe2 = self.obtener_datos_sp(self.conexion_ct2, 'DAC_D_SP_GetFacturasDetalles')

    def procesar_inventario(self):
        # Asumiendo que 'obtener_fechas_del_mes' y 'obtener_mes_anterior' son funciones definidas y accesibles
        fecha_inicio_actual, fecha_final_actual = self.obtener_fechas_del_mes(self.mes, self.anio)
        mes_anterior, anio_anterior = self.obtener_mes_anterior(self.mes, self.anio)
        fecha_inicio_anterior, fecha_final_anterior = self.obtener_fechas_del_mes(mes_anterior, anio_anterior)

        registros_mes_actual = self.dataframe1[(self.dataframe1['mes'] == self.mes) & (self.dataframe1['anio'] == self.anio)]
        registros_mes_anterior = self.dataframe1[(self.dataframe1['mes'] == mes_anterior) & (self.dataframe1['anio'] == anio_anterior)]

        for _, registro_actual in registros_mes_actual.iterrows():
            existencia_mes_actual = registro_actual['existencia']
            costo_mes_actual = registro_actual['costo']
            saldo_mes_actual = existencia_mes_actual * costo_mes_actual
            registro_anterior = registros_mes_anterior[registros_mes_anterior['id_equivalencia_x_categoria'] == registro_actual['id_equivalencia_x_categoria']]

            saldo_mes_anterior = 0
            if not registro_anterior.empty:
                existencia_mes_anterior = registro_anterior['existencia'].iloc[0]
                costo_mes_anterior = registro_anterior['costo'].iloc[0]
                saldo_mes_anterior = existencia_mes_anterior * costo_mes_anterior

            nuevo_registro = {
                'descripcion_producto': registro_actual['descripcion_producto'],
                'id_equivalencia_x_categoria': registro_actual['id_equivalencia_x_categoria'],
                'saldo_mes_actual': saldo_mes_actual,
                'saldo_mes_anterior': saldo_mes_anterior
            }
            self.resultados = self.resultados.append(nuevo_registro, ignore_index=True)

    def procesar_compras(self):
        self.dataframe2['fecha_ingreso'] = pd.to_datetime(self.dataframe2['fecha_ingreso'])
        self.dataframe2.sort_values(by=['id_equivalencia_x_categoria', 'fecha_ingreso'], inplace=True)

        diferencia_tiempo = self.dataframe2.groupby('id_equivalencia_x_categoria')['fecha_ingreso'].diff().shift(-1)
        self.dataframe2['dias_hasta_siguiente_compra'] = diferencia_tiempo.dt.days.fillna(0)

        ultimo_dia_del_mes = pd.to_datetime(self.obtener_fechas_del_mes(self.mes, self.anio)[1]) + MonthEnd(0)
        ultima_compra_indices = self.dataframe2.groupby('id_equivalencia_x_categoria')['fecha_ingreso'].idxmax()
        self.dataframe2.loc[ultima_compra_indices, 'dias_hasta_siguiente_compra'] = (ultimo_dia_del_mes - self.dataframe2.loc[ultima_compra_indices, 'fecha_ingreso']).dt.days + 1

        self.dataframe2['total_producto_ponderado'] = self.dataframe2['total_producto'] * self.dataframe2['dias_hasta_siguiente_compra']

    def calcular_metricas(self):
        numero_dias_mes = Decimal((self.obtener_fechas_del_mes(self.mes, self.anio)[1] - self.obtener_fechas_del_mes(self.mes, self.anio)[0]).days + 1)
        self.resultados_final['inventario_promedio'] = (self.resultados_final['saldo_mes_actual'] + self.resultados_final['saldo_mes_anterior'] + self.resultados_final['suma_total_producto_ponderado']) / numero_dias_mes
        self.resultados_final['COGS'] = self.resultados_final['total_producto'] + (self.resultados_final['saldo_mes_actual'] - self.resultados_final['saldo_mes_anterior'])
        self.resultados_final['rotacion_de_inventario_promedio'] = np.where(
            self.resultados_final['inventario_promedio'] != 0,
            self.resultados_final['COGS'] / self.resultados_final['inventario_promedio'],
            0
        )

    def obtener_rotacion_producto(self):
        try:
            self.cargar_datos()
            self.procesar_inventario()
            self.procesar_compras()
            self.calcular_metricas()
            return self.resultados_final
        except Exception as e:
            print("Ocurrió un error al obtener los datos:", e)
            return pd.DataFrame()

