import pyodbc

try:
    # Conexión a SQL Server
    sqlserver_conn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};SERVER=ZEUS\\SQLEXPRESS;DATABASE=biometricos;UID=csolano;PWD=Qaz*123'
    )
    print("Conexión a SQL Server exitosa")
    sqlserver_cursor = sqlserver_conn.cursor()

    # Conexión a MySQL usando DSN
    mysql_conn = pyodbc.connect('DSN=linode')
    print("Conexión a MySQL exitosa")
    mysql_cursor = mysql_conn.cursor()

    # Ejecutar consulta en SQL Server
    sqlserver_cursor.execute("""
        SELECT 
            [Userid],      -- Mapeado a Userid en MySQL
            [Name],        -- Mapeado a Name en MySQL
            [Deptid]       -- Mapeado a Deptid en MySQL
        FROM [biometricos].[dbo].[Userinfo]
    """)
    rows = sqlserver_cursor.fetchall()

    # Insertar datos en MySQL
    for row in rows:
        mysql_cursor.execute("""
            INSERT INTO universal_dev2.th_info_empleado_biometrico_temporal (
                Userid,
                Name,
                Deptid
            ) 
            VALUES (?, ?, ?, ?, ?)
        """, 
        (
            row.Userid,         # Userid
            row.Name,           # Name
            row.Deptid
        ))

    # Confirmar los cambios en MySQL
    mysql_conn.commit()
    print("Datos transferidos exitosamente")

except Exception as e:
    print(f"Error: {e}")

finally:
    # Cerrar conexiones si están abiertas
    try:
        sqlserver_conn.close()
        print("Conexión a SQL Server cerrada")
    except:
        pass

    try:
        mysql_conn.close()
        print("Conexión a MySQL cerrada")
    except:
        pass
