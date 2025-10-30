import requests
import adodbapi



def get_laravel_content(site):
    url = site
    response = requests.get(site)
    if response.status_code == 200:
        return response.text
    else:
        return 'Contenido no disponible'


class FoxProConnection:
    def __init__(self, db_path):
        self.connection_string = (
            "Provider=VFPOLEDB.1;"
            "Data Source=" + db_path + ";"
            "Mode=ReadWrite;"
        )
        self.conn = None

    def connect(self):
        """Establece la conexión a la base de datos de FoxPro."""
        self.conn = adodbapi.connect(self.connection_string)

    def disconnect(self):
        """Cierra la conexión a la base de datos de FoxPro."""
        if self.conn:
            self.conn.close()

    def execute_query(self, query, params=()):
        """
        Ejecuta una consulta `SELECT` en la base de datos de FoxPro.
        
        Args:
            query (str): La consulta SQL a ejecutar.
            params (tuple): Parámetros opcionales para la consulta.

        Returns:
            list: Lista de filas obtenidas en la consulta.
        """
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def get_column_names(self, query, params=()):
        """
        Ejecuta una consulta para obtener los nombres de las columnas dinámicamente.
        
        Args:
            query (str): La consulta SQL a ejecutar para obtener las columnas.
            params (tuple): Parámetros opcionales para la consulta.

        Returns:
            list: Lista de nombres de las columnas de la consulta.
        """
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        column_names = [desc[0] for desc in cursor.description]
        return column_names
