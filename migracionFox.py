import logging
import os 
import pandas as pd
import adodbapi
import pymysql
from datetime import datetime, timedelta
import time

# Tamaño de cada archivo CSV
registros_por_archivo = 10000  


# Configuración del logger para el directorio específico
log_directory = r'C:\Users\Administrador\Documents\PYTHON\ScriptFox\logs'  # Especifica la ruta completa
os.makedirs(log_directory, exist_ok=True)  # Crear la carpeta si no existe
log_filename = datetime.now().strftime("log_%Y%m%d_%H%M%S.txt")  # Nombre del archivo con fecha y hora
log_filepath = os.path.join(log_directory, log_filename)


logging.basicConfig(
    filename=log_filepath,
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class FoxProConnection:
    def __init__(self, db_path, max_retries=5, delay=2):
        self.connection_string = (
            "Provider=VFPOLEDB.1;"
            "Data Source=" + db_path + ";"
            "Mode=ReadWrite;"
        )
        self.conn = None
        self.max_retries = max_retries
        self.delay = delay  # segundos entre reintentos

    def connect(self):
        """Intenta establecer la conexión a la base de datos de FoxPro con reintentos."""
        attempts = 0
        while attempts < self.max_retries:
            try:
                self.conn = adodbapi.connect(self.connection_string)
                print("Conexión establecida exitosamente.")
                return
            except adodbapi.OperationalError as e:
                print("Error de conexión: {}. Intento {}/{}".format(e, attempts + 1, self.max_retries))
                attempts += 1
                time.sleep(self.delay)
                continue
        raise ConnectionError("No se pudo conectar a la base de datos de FoxPro después de varios intentos.")
    
    def disconnect(self):
        """Cierra la conexión a la base de datos de FoxPro."""
        if self.conn:
            try:
                self.conn.close()
                print("Conexión cerrada correctamente.")
            except Exception as e:
                print("Error al cerrar la conexión: {}".format(e))

    def execute_query(self, query, params=()):
        """Ejecuta una consulta SELECT en la base de datos de FoxPro."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        finally:
            cursor.close()  # Asegura que el cursor se cierre después de su uso

    def get_column_names(self, query, params=()):
        """Obtiene los nombres de las columnas de una consulta en FoxPro."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            column_names = [desc[0] for desc in cursor.description]
            return column_names
        finally:
            cursor.close()


def calcular_fecha_dias_atras(dias_hacia_atras):
    """Calcula la fecha límite hacia atrás a partir de la fecha actual."""
    return (datetime.now() - timedelta(days=dias_hacia_atras)).strftime('%Y-%m-%d')

def limpiar_fechas(df, columnas_fecha):
    """
    Limpia las fechas no válidas en las columnas especificadas de un DataFrame.
    Reemplaza las fechas incorrectas (como '1899-12-30 00:00:00') con `NaT` (Not a Time).
    
    Args:
        df (pd.DataFrame): El DataFrame con los datos a limpiar.
        columnas_fecha (list): Lista de nombres de las columnas de fecha a limpiar.

    Returns:
        pd.DataFrame: DataFrame con fechas no válidas reemplazadas por `NaT`.
    """
    for columna in columnas_fecha:
        # Convertir la columna a datetime y forzar errores a NaT para valores inválidos
        df[columna] = pd.to_datetime(df[columna], errors='coerce')
        
        # Reemplazar la fecha específica '1899-12-30' con NaT
        df[columna] = df[columna].apply(lambda x: pd.NaT if x == pd.Timestamp('1899-12-30') else x)
    
    return df


def obtener_datos_por_fecha(tabla, dias_hacia_atras, ruta_dbf, batch_size=1000):
    """Extrae los datos de FoxPro desde una fecha base hacia atrás en días especificados, en lotes pequeños."""
    var_fecha = calcular_fecha_dias_atras(dias_hacia_atras)
    fecha_actual = calcular_fecha_dias_atras(0)
    
    fox_conn = FoxProConnection(ruta_dbf)
    try:
        fox_conn.connect()
        cursor = fox_conn.conn.cursor()
        
            # Query para obtener datos en lotes
        query = """
        SELECT * FROM {}
        WHERE (fecha_ingreso >= {{^{} }} OR fecha_modificacion = {{^{} }})
        """.format(tabla, var_fecha, fecha_actual)

        
        cursor.execute(query)
        registros = []
        
        # Obtener datos en lotes
        while True:
            batch = cursor.fetchmany(batch_size)
            if not batch:
                break  # Salimos si no hay más datos
            registros.extend(batch)  # Añadir el lote al resultado final
        
        columnas = [desc[0] for desc in cursor.description]
    finally:
        cursor.close()
        fox_conn.disconnect()
    return pd.DataFrame(registros, columns=columnas)

def obtener_datos_descuentos(tabla, dias_hacia_atras, ruta_dbf, batch_size=1000):
    """Extrae los datos de FoxPro desde una fecha base hacia atrás en días especificados, en lotes pequeños."""
    var_fecha = calcular_fecha_dias_atras(dias_hacia_atras)
    fecha_actual = calcular_fecha_dias_atras(0)
    
    fox_conn = FoxProConnection(ruta_dbf)
    try:
        fox_conn.connect()
        cursor = fox_conn.conn.cursor()
        
            # Query para obtener datos en lotes
        query = """
        SELECT * FROM {}
        WHERE fecha_nc >= {{^{} }}
        """.format(tabla, var_fecha)

        
        cursor.execute(query)
        registros = []
        
        # Obtener datos en lotes
        while True:
            batch = cursor.fetchmany(batch_size)
            if not batch:
                break  # Salimos si no hay más datos
            registros.extend(batch)  # Añadir el lote al resultado final
        
        columnas = [desc[0] for desc in cursor.description]
    finally:
        cursor.close()
        fox_conn.disconnect()
    return pd.DataFrame(registros, columns=columnas)



def obtener_datos_completos(tabla, ruta_dbf):
    """Extrae todos los registros de una tabla en FoxPro."""
    fox_conn = FoxProConnection(ruta_dbf)
    try:
        fox_conn.connect()
        cursor = fox_conn.conn.cursor()
        query = "SELECT * FROM {}".format(tabla)
        cursor.execute(query)
        registros = cursor.fetchall()
        columnas = [desc[0] for desc in cursor.description]
    finally:
        cursor.close()
        fox_conn.disconnect()
    return pd.DataFrame(registros, columns=columnas)


def dividir_y_guardar_csv(df, nombre_tabla, ruta_csv_tabla):
    """Divide y guarda el DataFrame en archivos CSV de tamaño especificado."""
    archivo_contador = 1
    num_registros = len(df)
    rutas_csv = []
    for i in range(0, num_registros, registros_por_archivo):
        df_temporal = df.iloc[i:i + registros_por_archivo]
        ruta_csv_archivo = "{}\\{}_parte{}.csv".format(ruta_csv_tabla, nombre_tabla, archivo_contador)
        df_temporal.to_csv(ruta_csv_archivo, index=False, date_format='%Y-%m-%d %H:%M:%S')
        rutas_csv.append(ruta_csv_archivo)
        archivo_contador += 1
    return rutas_csv

def llamar_sp_crear_tabla(conexion, nombre_tabla):
    """Llama al stored procedure correspondiente para crear la tabla temporal en MySQL."""
    cursor = conexion.cursor()
    sp_name = "CALL FOX_temp_{}();".format(nombre_tabla)  # Nombre del stored procedure
    cursor.execute(sp_name)
    conexion.commit()
    cursor.close()

def cargar_csv_en_mysql(rutas_csv, nombre_tabla, tabla_id, conexion):
    """Carga los archivos CSV en la tabla temporal correspondiente en MySQL."""
    llamar_sp_crear_tabla(conexion, nombre_tabla)
    cursor = conexion.cursor()
    print("Creacion de tabla temporal {}.".format(nombre_tabla))

    # Cargar cada CSV en la tabla temporal
    for ruta_csv in rutas_csv:
        cargar_datos_sql = """
        LOAD DATA LOCAL INFILE '{}'
        INTO TABLE temp_{}
        FIELDS TERMINATED BY ','
        OPTIONALLY ENCLOSED BY '"'
        LINES TERMINATED BY '\\n'
        IGNORE 1 LINES;
        """.format(ruta_csv.replace("\\", "/"), nombre_tabla)
        cursor.execute(cargar_datos_sql)
        print("Datos cargados desde {} en temp_{}.".format(ruta_csv.replace("\\", "/"), nombre_tabla))
    
    # Ejecutar stored procedure para procesar los datos de la tabla temporal
    try:
        cursor.execute("CALL FOX_load_{}();".format(nombre_tabla))
        conexion.commit()
        cursor.close()
        print("Success FOX_load_{}()".format(nombre_tabla))
    except Exception as e:
        print("Error FOX_load_{}() {}".format(nombre_tabla, str(e)))

def migrar_tabla(tabla, dias_hacia_atras=None, tabla_id=1, completa=False, ruta_dbf=None, ruta_csv=None):
    """
    Migrar una tabla de FoxPro a MySQL.
    - Si `completa` es True, trae todos los registros de la tabla.
    - Si `completa` es False, aplica un filtro de días hacia atrás usando `dias_hacia_atras`.
    """
    start_time_obtener_datos = time.time()

    if completa:
        df = obtener_datos_completos(tabla, ruta_dbf)
    else:
        df = obtener_datos_por_fecha(tabla, dias_hacia_atras, ruta_dbf)

    end_time_obtener_datos = time.time()
    formatted_elapsed_time_obtener_datos = "{:.2f}".format(end_time_obtener_datos - start_time_obtener_datos)
    print("")
    print("Tiempo de Obtener Datos: {} para {}.".format(formatted_elapsed_time_obtener_datos, tabla))
    
    # Dividir y guardar en archivos CSV en la ruta especificada
    start_time_dividir_excel = time.time()
    rutas_csv = dividir_y_guardar_csv(df, tabla, ruta_csv)
    end_time_dividir_excel = time.time()
    formatted_elapsed_time_dividir_excel = "{:.2f}".format(end_time_dividir_excel - start_time_dividir_excel)
    print("Tiempo de Dividir Excel: {} para {}.".format(formatted_elapsed_time_dividir_excel, tabla))

    # Conectar a MySQL y cargar los archivos CSV
    conexion = pymysql.connect(user='root', password='$Admincarba24*_', host='3.230.160.184', database='universal_data_core', local_infile=True)
    cargar_csv_en_mysql(rutas_csv, tabla, tabla_id, conexion)
    conexion.close()

    # Eliminar archivos CSV una vez procesados
    for ruta_csv in rutas_csv:
        #os.remove(ruta_csv)
        print("Archivo {} eliminado después de cargar en MySQL.".format(ruta_csv))
    print("")

    
def migrar_tabla_descuentos(tabla, dias_hacia_atras=None, tabla_id=1, completa=False, ruta_dbf=None, ruta_csv=None):
    """
    Migrar una tabla de FoxPro a MySQL.
    - Si `completa` es True, trae todos los registros de la tabla.
    - Si `completa` es False, aplica un filtro de días hacia atrás usando `dias_hacia_atras`.
    """
    start_time_obtener_datos = time.time()

    df = obtener_datos_descuentos(tabla, dias_hacia_atras, ruta_dbf) 

    end_time_obtener_datos = time.time()
    formatted_elapsed_time_obtener_datos = "{:.2f}".format(end_time_obtener_datos - start_time_obtener_datos)
    print("")
    print("Tiempo de Obtener Datos: {} para {}.".format(formatted_elapsed_time_obtener_datos, tabla))
    
    # Dividir y guardar en archivos CSV en la ruta especificada
    start_time_dividir_excel = time.time()
    rutas_csv = dividir_y_guardar_csv(df, tabla, ruta_csv)
    end_time_dividir_excel = time.time()
    formatted_elapsed_time_dividir_excel = "{:.2f}".format(end_time_dividir_excel - start_time_dividir_excel)
    print("Tiempo de Dividir Excel: {} para {}.".format(formatted_elapsed_time_dividir_excel, tabla))

    # Conectar a MySQL y cargar los archivos CSV
    conexion = pymysql.connect(user='root', password='$Admincarba24*_', host='3.230.160.184', database='universal_data_core', local_infile=True)
    cargar_csv_en_mysql(rutas_csv, tabla, tabla_id, conexion)
    conexion.close()

    # Eliminar archivos CSV una vez procesados
    for ruta_csv in rutas_csv:
        #os.remove(ruta_csv)
        print("Archivo {} eliminado después de cargar en MySQL.".format(ruta_csv))
    print("")

# Ejemplo de ejecución al ser llamado desde un .bat
if __name__ == "__main__":
    # Puedes modificar o eliminar los valores de ejemplo para ajustar al .bat
    # ('ft_facturas', 1, 50), ('ft_detalles', 1, 50),('iv_ruteo_ordenes_de_remision', 1, 50), ('iv_ruteo_ordenes_de_remision_detalle', 1, 50), ('mg_clientes', 1, 50), ('iv_unidades', 1, 50), ('iv_unidades_equivalencias_x_categoria', 1, 50), ('ft_facturas_al_credito', 1, 50), ('ft_facturas_al_credito_movimientos', 1, 100)
    tablas_con_rango = [('ft_notas_de_credito_a_factura', 1, 50)]
    
    tablas_completas = [('ft_descripcion_canal_venta', 1)]
    
    tablas_descuentos_detalle = [('ft_notas_de_credito_x_descuento_detalle', 1)]
    

    for tabla, tabla_id, dias_hacia_atras in tablas_con_rango:
        start_time = time.time()

        migrar_tabla(tabla, dias_hacia_atras=dias_hacia_atras, tabla_id=tabla_id, completa=False, ruta_dbf='G:\\CONTROL\\Base', ruta_csv='G:\\CONTROL\\Base\\csv\\' + tabla)

        end_time = time.time()
        formatted_elapsed_time = "{:.2f}".format(end_time - start_time)
        print("Tiempo de Ejecucion: {} para {}.".format(formatted_elapsed_time, tabla))
        
        log_message  = "Tiempo de Ejecucion: {} para {}.".format(formatted_elapsed_time, tabla)
        logging.info(log_message)

    for tabla, tabla_id in tablas_completas:
        start_time = time.time()
        
        migrar_tabla(tabla, tabla_id=tabla_id, completa=True, ruta_dbf='G:\\CONTROL\\Base', ruta_csv='G:\\CONTROL\\Base\\csv\\' + tabla + '\\')
        
        end_time = time.time()
        formatted_elapsed_time = "{:.2f}".format(end_time - start_time)
        print("Tiempo de Ejecucion: {} para {}.".format(formatted_elapsed_time, tabla))
        
        log_message  = "Tiempo de Ejecucion: {} para {}.".format(formatted_elapsed_time, tabla)
        logging.info(log_message)
 
    for tabla, tabla_id, dias_hacia_atras in tablas_descuentos_detalle:
        start_time = time.time()

        migrar_tabla_descuentos(tabla, dias_hacia_atras=dias_hacia_atras, tabla_id=tabla_id, completa=False, ruta_dbf='G:\\CONTROL\\Base', ruta_csv='G:\\CONTROL\\Base\\csv\\' + tabla)

        end_time = time.time()
        formatted_elapsed_time = "{:.2f}".format(end_time - start_time)
        print("Tiempo de Ejecucion: {} para {}.".format(formatted_elapsed_time, tabla))
        
        log_message  = "Tiempo de Ejecucion: {} para {}.".format(formatted_elapsed_time, tabla)
        logging.info(log_message)