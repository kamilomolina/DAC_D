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
    mysql_conn.autocommit = False  # Desactivar autocommit para control manual de transacciones
    print("Conexión a MySQL exitosa")
    mysql_cursor = mysql_conn.cursor()

    # **Paso 1: Transferir datos desde la tabla `Checkinout`**
    print("Transfiriendo datos de 'Checkinout'...")
    sqlserver_cursor.execute("""
        SELECT 
            [Logid],       
            [Userid],      
            [CheckTime],   
            [CheckType],   
            [Sensorid]  
        FROM [biometricos].[dbo].[Checkinout]
        WHERE [CheckTime] >= '2024-04-12 00:00:00'
        AND [CheckTime] < '2024-04-12 23:59:59'
    """)
    checkinout_rows = sqlserver_cursor.fetchall()

    # Inserciones por lotes
    batch_size = 100  # Tamaño del lote
    batch = []
    for i, row in enumerate(checkinout_rows, start=1):
        batch.append((
            row.Logid,
            row.Userid,
            row.CheckTime,
            row.CheckType,
            row.Sensorid
        ))

        if i % batch_size == 0 or i == len(checkinout_rows):
            try:
                print(f"Insertando lote con {len(batch)} registros...")
                mysql_cursor.executemany("""
                    INSERT INTO universal_data_core.th_registrosAcceso_biometrico (
                        Logid,
                        IdUsuario, 
                        FechaHoraAcceso, 
                        TipoAcceso, 
                        IdSensor
                    ) 
                    VALUES (?, ?, ?, ?, ?)
                """, batch)
                mysql_conn.commit()
                batch = []  # Limpiar el lote
            except pyodbc.Error as e:
                print(f"Error durante la inserción de lotes en 'Checkinout': {e}")
                mysql_conn.rollback()
                print("Lote fallido:", batch)  # Imprime el lote que falló

    print("Transferencia de 'Checkinout' completada.")

    # **Paso 2: Transferir datos desde la tabla `Userinfo`**
    print("Transfiriendo datos de 'Userinfo'...")
    sqlserver_cursor.execute("""
        SELECT 
            [Userid],      -- Mapeado a Userid en MySQL
            [Name],        -- Mapeado a Name en MySQL
            [Deptid]       -- Mapeado a Deptid en MySQL
        FROM [biometricos].[dbo].[Userinfo]
    """)
    userinfo_rows = sqlserver_cursor.fetchall()

    # Inserciones por lotes para `Userinfo`
    batch = []
    for i, row in enumerate(userinfo_rows, start=1):
        batch.append((
            row.Userid,
            row.Name,
            row.Deptid,
            'script_migracion',  # creado_por
            1                   # estado
        ))

        if i % batch_size == 0 or i == len(userinfo_rows):
            try:
                print(f"Insertando lote con {len(batch)} registros en 'Userinfo'...")
                mysql_cursor.executemany("""
                    INSERT INTO universal_dev2.th_info_empleado_biometrico (
                        Userid,
                        Name,
                        Deptid,
                        creado_por,
                        estado
                    ) 
                    VALUES (?, ?, ?, ?, ?)
                """, batch)
                mysql_conn.commit()
                batch = []  # Limpiar el lote
            except pyodbc.Error as e:
                print(f"Error durante la inserción de lotes en 'Userinfo': {e}")
                mysql_conn.rollback()

    print("Transferencia de 'Userinfo' completada.")

    # Confirmar los cambios en MySQL
    mysql_conn.commit()
    print("Todos los datos fueron transferidos exitosamente.")

except Exception as e:
    print(f"Error general: {e}")

finally:
    # Cerrar conexiones si están abiertas
    try:
        sqlserver_conn.close()
        print("Conexión a SQL Server cerrada")
    except Exception as e:
        print(f"Error cerrando conexión SQL Server: {e}")

    try:
        mysql_conn.close()
        print("Conexión a MySQL cerrada")
    except Exception as e:
        print(f"Error cerrando conexión MySQL: {e}")
