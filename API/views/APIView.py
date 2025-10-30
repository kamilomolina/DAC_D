from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.db import connections
from django.http import JsonResponse
from django.conf import settings
from datetime import datetime, timedelta
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import sessionmaker
import time
import pymysql
import requests
from requests.exceptions import HTTPError
import hashlib
import subprocess
import jwt
from urllib.parse import quote_plus
import json
from django.core.mail import send_mail
from django.urls import reverse
from django.template.loader import render_to_string


TOKEN = '2e078366ee3366544e4132ebb24eb2948270bbce69aa8ff22a30a2422cc12a7e'
FORMATO_DEFAULT = 1
AGRUPACION_PROVEEDORES = 1


class SetPrincipalArticulosProveedorSupermercado(APIView):
    def post(self, request, *args, **kwargs):

        auth_header = request.headers.get('API-Token', None)
        if auth_header:
            parts = auth_header.split()
            if auth_header != TOKEN:
                return Response({"error": "Token no válido o formato de autorización incorrecto."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"error": "No se proporcionó token de autorización."}, status=status.HTTP_401_UNAUTHORIZED)

        secuencia_id = request.POST.get('secuencia_id')

        try:
            createdConn = connections['super']
            with defaultConn.cursor() as cursor:
                cursor.callproc('DAC_SET_ARTICULO_PROVEEDOR_PRINCIPAL', [secuencia_id])
                results = cursor.fetchall()

            # Cierra la conexión
            createdConn.close()
            
            # Devuelve los resultados como JSON
            datos = {'save': 1}
        except Exception as e:
            datos = {'save': 0, 'error': str(e)}
        
        return JsonResponse(datos)


class ArticulosProveedoresSupermercadoData(APIView):
    def post(self, request, *args, **kwargs):

        auth_header = request.headers.get('API-Token', None)
        if auth_header:
            parts = auth_header.split()
            if auth_header != TOKEN:
                return Response({"error": "Token no válido o formato de autorización incorrecto."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"error": "No se proporcionó token de autorización."}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            defaultConn = connections['super']
            with defaultConn.cursor() as cursor:
                cursor.callproc('DAC_GET_ARTICULOS_PROVEEDORES')
                column_names = [desc[0] for desc in cursor.description]
                articulosProveedoresData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
            # Cierra la conexión
            defaultConn.close()
            
            # Devuelve los resultados como JSON
            return JsonResponse({'data': articulosProveedoresData})
        except Exception as e:
            # Manejo de excepciones, puedes personalizar esto según tus necesidades
            return JsonResponse({'error': str(e)})


class ReporteRankingProveedores(APIView):
    def post(self, request, *args, **kwargs):

        auth_header = request.headers.get('API-Token', None)
        if auth_header:
            parts = auth_header.split()
            if auth_header != TOKEN:
                return Response({"error": "Token no válido o formato de autorización incorrecto."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"error": "No se proporcionó token de autorización."}, status=status.HTTP_401_UNAUTHORIZED)

        proveedor = request.POST.get('proveedor')
        producto = request.POST.get('producto')
        almacen = request.POST.get('almacen')
        date1 = request.POST.get('date1')
        date2 = request.POST.get('date2')

        formato = int(request.POST.get('formato', FORMATO_DEFAULT))
        agrupacion = int(request.POST.get('agrupacion', AGRUPACION_PROVEEDORES))
        
        if formato == FORMATO_DEFAULT:
            conn = "default"
        else:
            conn = "super"

        if agrupacion == AGRUPACION_PROVEEDORES:
            stored_procedure = "DAC_REPORTE_RANKING_PROVEEDORES"
        else:
            stored_procedure = "DAC_REPORTE_RANKING_PROVEEDORES_DETAILS_v2"

        try:
            defaultConn = connections[conn]
            with defaultConn.cursor() as cursor:
                cursor.callproc(stored_procedure, [almacen, proveedor, producto, date1, date2])
                column_names = [desc[0] for desc in cursor.description]
                rankingProveedoresData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
            # Cierra la conexión
            defaultConn.close()
            
            # Devuelve los resultados como JSON
            return JsonResponse({'data': rankingProveedoresData})
        except Exception as e:
            # Manejo de excepciones, puedes personalizar esto según tus necesidades
            return JsonResponse({'error': str(e)})


class ReporteRankingProveedoresDetalles(APIView):
    def post(self, request, *args, **kwargs):

        auth_header = request.headers.get('API-Token', None)
        if auth_header:
            parts = auth_header.split()
            if auth_header != TOKEN:
                return Response({"error": "Token no válido o formato de autorización incorrecto."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"error": "No se proporcionó token de autorización."}, status=status.HTTP_401_UNAUTHORIZED)

        proveedor = request.POST.get('proveedor')
        producto = request.POST.get('producto')
        almacen = request.POST.get('almacen')
        date1 = request.POST.get('date1')
        date2 = request.POST.get('date2')

        try:
            defaultConn = connections['default']
            with defaultConn.cursor() as cursor:
                cursor.callproc("DAC_REPORTE_RANKING_PROVEEDORES_DETAILS_v2", [almacen, proveedor, producto, date1, date2])
                column_names = [desc[0] for desc in cursor.description]
                rankingProveedoresDetallesData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
            # Cierra la conexión
            defaultConn.close()
            
            # Devuelve los resultados como JSON
            return JsonResponse({'data': rankingProveedoresDetallesData})
        except Exception as e:
            # Manejo de excepciones, puedes personalizar esto según tus necesidades
            return JsonResponse({'error': str(e)})


class updateSaldosMovil(APIView):
    def get(self, request, *args, **kwargs):

        auth_header = request.headers.get('API-Token', None)
        if auth_header:
            parts = auth_header.split()
            if auth_header != TOKEN:
                return Response({"error": "Token no válido o formato de autorización incorrecto."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"error": "No se proporcionó token de autorización."}, status=status.HTTP_401_UNAUTHORIZED)
        
        start_time_p = time.time()
        start_time = time.time()

        error_list = []

        password = '$Carba_admin*20'
        engine_source = create_engine('mysql+pymysql://root:{}@190.4.11.58/super_carbajal'.format(password))

        time.sleep(2)

        articulos_bodega = None
        articulos = None
        clientes = None
        presentaciones = None
        subgrupos = None
        medidas = None
        articulos_escalas = None
        grupos = None

        try:
            articulos_bodega = pd.read_sql('CALL API_UPDATE_SALDOS_MOVIL()', con=engine_source)
        except Exception as e: 
            print("Error Articulos Bodega Data ", format(str(e)))
            error_info = {
                "asunto": "Error Articulos Bodega Data",
                "descripcion": str(e),
                "maquina": "SUPER-DC"
            }
            error_list.append(error_info)

        try:
            articulos = pd.read_sql('CALL SZ_GET_ARTICULOS_ALL()', con=engine_source)
        except Exception as e: 
            print("Error Articulos Data ", format(str(e)))
            error_info = {
                "asunto": "Error Articulos Data",
                "descripcion": str(e),
                "maquina": "SUPER-DC"
            }
            error_list.append(error_info)

        try:
            clientes = pd.read_sql('CALL SZ_GET_CLIENTES_ALL()', con=engine_source)
        except Exception as e: 
            print("Error Clientes Data ", format(str(e)))
            error_info = {
                "asunto": "Error Clientes Data",
                "descripcion": str(e),
                "maquina": "SUPER-DC"
            }
            error_list.append(error_info)

        try:
            presentaciones = pd.read_sql('CALL SZ_GET_PRESENTACIONES_ALL()', con=engine_source)
        except Exception as e: 
            print("Error Presentaciones Data ", format(str(e)))
            error_info = {
                "asunto": "Error Presentaciones Data",
                "descripcion": str(e),
                "maquina": "SUPER-DC"
            }
            error_list.append(error_info)

        try:
            grupos = pd.read_sql('CALL SZ_GET_GRUPOS_ALL()', con=engine_source)
        except Exception as e: 
            print("Error Grupos Data ", format(str(e)))
            error_info = {
                "asunto": "Error Grupos Data",
                "descripcion": str(e),
                "maquina": "SUPER-DC"
            }
            error_list.append(error_info)

        try:
            subgrupos = pd.read_sql('CALL SZ_GET_SUBGRUPOS_ALL()', con=engine_source)
        except Exception as e: 
            print("Error Subgrupos Data ", format(str(e)))
            error_info = {
                "asunto": "Error Subgrupos Data",
                "descripcion": str(e),
                "maquina": "SUPER-DC"
            }
            error_list.append(error_info)

        try:
            medidas = pd.read_sql('CALL SZ_GET_MEDIDAS_ALL()', con=engine_source)
        except Exception as e: 
            print("Error Medidas Data ", format(str(e)))
            error_info = {
                "asunto": "Error Medidas Data",
                "descripcion": str(e),
                "maquina": "SUPER-DC"
            }
            error_list.append(error_info)

        try:
            articulos_escalas = pd.read_sql('CALL SZ_GET_ARTICULOS_ESCALA_ALL()', con=engine_source)
        except Exception as e: 
            print("Error Articulos Escala Data ", format(str(e)))
            error_info = {
                "asunto": "Error Articulos Escala Data",
                "descripcion": str(e),
                "maquina": "SUPER-DC"
            }
            error_list.append(error_info)




        end_time_p = time.time()
        formatted_elapsed_time_p = "{:.2f}".format(end_time_p - start_time_p)
        print("Get Data Elapsed Time:", formatted_elapsed_time_p)
        
        password2 = '$Carba_admin*20'
        engine_destination = create_engine('mysql+pymysql://root:{}@190.4.11.58/pedidos_posca'.format(password2))

        with engine_destination.connect() as conn:
            transaction = conn.begin()
            try:
                tables = [
                    "articulos_bodega", "articulos", "clientes", "presentaciones", "grupos", "subgrupos", "medidas", "articulos_escalas"
                ]
                for table in tables:
                    conn.execute(text("TRUNCATE TABLE {}".format(table)))
                transaction.commit()
            except Exception as e:
                print("Error en TRUNCATE TABLES", str(e))
                error_info = {
                    "asunto": "Error en TRUNCATE TABLES",
                    "descripcion": str(e),
                    "maquina": "SUPER-DC"
                }
                error_list.append(error_info)

            time.sleep(2)

            if articulos_bodega is not None:
                try:
                    articulos_bodega.to_sql('articulos_bodega', engine_destination, index=False, if_exists='append', chunksize=1000)
                except Exception as e:
                    print("Error al insertar datos Articulos Bodega Super DC Nube", format(str(e)))
                    error_info = {
                        "asunto": "Error al insertar datos Articulos Bodega Super DC Nube",
                        "descripcion": str(e),
                        "maquina": "ge"
                    }
                    error_list.append(error_info)

            if clientes is not None:
                try:
                    clientes.to_sql('clientes', engine_destination, index=False, if_exists='append', chunksize=1000)
                except Exception as e:
                    print("Error al insertar datos Clientes Super DC Nube", format(str(e)))
                    error_info = {
                        "asunto": "Error al insertar datos Clientes Super DC Nube",
                        "descripcion": str(e),
                        "maquina": "ge"
                    }
                    error_list.append(error_info)

            if presentaciones is not None:
                try:
                    presentaciones.to_sql('presentaciones', engine_destination, index=False, if_exists='append', chunksize=1000)
                except Exception as e:
                    print("Error al insertar datos Presentaciones Super DC Nube", format(str(e)))
                    error_info = {
                        "asunto": "Error al insertar datos Presentaciones Super DC Nube",
                        "descripcion": str(e),
                        "maquina": "ge"
                    }
                    error_list.append(error_info)

            if grupos is not None:
                try:
                    grupos.to_sql('grupos', engine_destination, index=False, if_exists='append', chunksize=1000)
                except Exception as e:
                    print("Error al insertar datos Grupos Super DC Nube", format(str(e)))
                    error_info = {
                        "asunto": "Error al insertar datos Grupos Super DC Nube",
                        "descripcion": str(e),
                        "maquina": "ge"
                    }
                    error_list.append(error_info)

            if subgrupos is not None:
                try:
                    subgrupos.to_sql('subgrupos', engine_destination, index=False, if_exists='append', chunksize=1000)
                except Exception as e:
                    print("Error al insertar datos Subgrupos Super DC Nube", format(str(e)))
                    error_info = {
                        "asunto": "Error al insertar datos Subgrupos Super DC Nube",
                        "descripcion": str(e),
                        "maquina": "ge"
                    }
                    error_list.append(error_info)

            if medidas is not None:
                try:
                    medidas.to_sql('medidas', engine_destination, index=False, if_exists='append', chunksize=1000)
                except Exception as e:
                    print("Error al insertar datos Medidas Super DC Nube", format(str(e)))
                    error_info = {
                        "asunto": "Error al insertar datos Medidas Super DC Nube",
                        "descripcion": str(e),
                        "maquina": "ge"
                    }
                    error_list.append(error_info)

            if articulos_escalas is not None:
                try:
                    articulos_escalas.to_sql('articulos_escalas', engine_destination, index=False, if_exists='append', chunksize=1000)
                except Exception as e:
                    print("Error al insertar datos Articulos Escala Super DC Nube", format(str(e)))
                    error_info = {
                        "asunto": "Error al insertar datos Articulos Escala Super DC Nube",
                        "descripcion": str(e),
                        "maquina": "ge"
                    }
                    error_list.append(error_info)

            if articulos is not None:
                try:
                    articulos.to_sql('articulos', engine_destination, index=False, if_exists='append', chunksize=1000)
                except Exception as e:
                    print("Error al insertar datos Articulos Super DC Nube", format(str(e)))
                    error_info = {
                        "asunto": "Error al insertar datos Articulos Super DC Nube",
                        "descripcion": str(e),
                        "maquina": "ge"
                    }
                    error_list.append(error_info)



        end_time = time.time()
        formatted_elapsed_time = "{:.2f}".format(end_time - start_time)
        print("Process Complete Elapsed Time:", formatted_elapsed_time)

        return JsonResponse({'success': True, 'time': formatted_elapsed_time, "error": len(error_list)})


class UpdateCAINumeroIngresado(APIView):
    def get(self, request, maquina, *args, **kwargs):

        auth_header = request.headers.get('API-Token', None)
        if auth_header:
            parts = auth_header.split()
            if auth_header != TOKEN:
                return Response({"error": "Token no válido o formato de autorización incorrecto."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"error": "No se proporcionó token de autorización."}, status=status.HTTP_401_UNAUTHORIZED)
        
        start_time_p = time.time()
        start_time = time.time()

        error_list = []

        password = '$Carba_admin*20'
        engine_source = create_engine('mysql+pymysql://root:{}@190.4.11.58/super_carbajal'.format(password))

        try:
            config_facturacion = pd.read_sql('CALL SZ_GET_CONFIG_FACTURACION_ALL()', con=engine_source)
        except Exception as e:
            print("Error Config Facturacion ", format(str(e)))
            error_info = {
                "asunto": "Error Config Facturacion Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)


        try:
            facturas_ingresadas = pd.read_sql('CALL SZ_GET_FACTURAS_INGRESADAS_CAI()', con=engine_source)
        except Exception as e:
            print("Error Facturas Ingresadas ", format(str(e)))
            error_info = {
                "asunto": "Error Facturas Ingresadas Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            nc_ingresadas = pd.read_sql('CALL SZ_GET_NOTAS_CREDITO_INGRESADAS_CAI()', con=engine_source)
        except Exception as e:
            print("Error Notas Credito Ingresadas ", format(str(e)))
            error_info = {
                "asunto": "Error Notas Credito Ingresadas Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            nd_ingresadas = pd.read_sql('CALL SZ_GET_NOTAS_DEBITO_INGRESADAS_CAI()', con=engine_source)
        except Exception as e:
            print("Error Notas Debito Ingresadas ", format(str(e)))
            error_info = {
                "asunto": "Error Notas Debito Ingresadas Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        end_time_p = time.time()
        formatted_elapsed_time_p = "{:.2f}".format(end_time_p - start_time_p)
        print("Get Data Elapsed Time:", formatted_elapsed_time_p)

        try:
            superNube = connections['super']
            with superNube.cursor() as cursor:  
                cursor.callproc("SZ_GET_MAQUINAS_DATA_ALL", [maquina])
                column_names = [desc[0] for desc in cursor.description]
                databases = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]

                if databases:
                    for db in databases:
                        try:
                            PKconfig = db['PKconfig']
                            maquina = db['Maquina']
                            password = quote_plus(db['m_password'])
                            bodega = db['m_bodega']
                            engine_destination_str = 'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'.format(
                                user=db['m_user'],
                                password=password,
                                host=db['m_host'],
                                port=db['m_port'],
                                database=db['m_database']
                            )
                            engine_destination = create_engine(engine_destination_str)


                            Session = sessionmaker(bind=engine_destination)
                            session = Session()

                            
                            try:
                                result = session.execute("CALL SZ_GET_STATUS_MAQUINA_LOCAL(:param)", {'param': PKconfig})
                                local = result.fetchone()[0] if result.returns_rows else None
                                session.commit()

                                if local == 1:
                                    local_mode = 'LOCAL'
                                    descripcion_text = 'DEBE SUBIR DATOS Y CAMBIAR A MODO SERVIDOR'
                                else:
                                    local_mode = 'SERVIDOR'
                                    descripcion_text = 'FUNCIONANDO CORRECTAMENTE'

                                print("Conexion a Maquina ", maquina, " en Modo ", local_mode)
                            except SQLAlchemyError as e:
                                print("Error en Conexion de Maquina ", maquina)
                                local == 3
                            finally:
                                session.close() 

                            if local == 0:
                                with engine_destination.connect() as conn:
                                    transaction = conn.begin()
                                    try:
                                        conn.execute("TRUNCATE TABLE configuracion_facturacion;")
                                        
                                        transaction.commit()
                                    except Exception as e:
                                        print("Error en TRUNCATE TABLES", str(e))
                                        error_info = {
                                            "asunto": "Error en TRUNCATE TABLES",
                                            "descripcion": str(e),
                                            "maquina": maquina
                                        }
                                        error_list.append(error_info)

                                try:
                                    config_facturacion.to_sql('configuracion_facturacion', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Config Facturacion ", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Config Facturacion",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)


                                if not facturas_ingresadas.empty:
                                    for factura in facturas_ingresadas.itertuples():
                                        numero = factura.numero_factura 
                                        ingresado_por = factura.ingresado_por 
                                        if pd.isna(factura.fecha_ingreso):
                                            fecha_ingreso = None
                                        else:
                                            fecha_ingreso = factura.fecha_ingreso.to_pydatetime()
                                        sistema = factura.sistema 
                                        fkCAI = factura.fkCAI 
                                        InicioCAI = 1
                                        opcion = 1

                                        Session = sessionmaker(bind=engine_destination)
                                        session = Session()
                                        
                                        try:
                                            session.execute(
                                                    "CALL SZ_INSERT_INICIO_CAI_LOCAL(:opcion, :numero, :usuario, :fecha, :sistema, :cai, :inicio)", 
                                                    {
                                                        'opcion': opcion, 
                                                        'numero': numero, 
                                                        'usuario': ingresado_por, 
                                                        'fecha': fecha_ingreso, 
                                                        'sistema': sistema, 
                                                        'cai': fkCAI, 
                                                        'inicio': InicioCAI
                                                    }
                                                )
                                            session.commit()
                                        except SQLAlchemyError as e:
                                            session.rollback()
                                            print("Error durante la inserción de facturas:", str(e))
                                        except Exception as e:
                                            session.rollback()
                                            print("Error inesperado:", str(e))
                                        finally:
                                            session.close()


                                if not nc_ingresadas.empty:
                                    for nc in nc_ingresadas.itertuples():
                                        numero = nc.numero_nota 
                                        ingresado_por = nc.ingresado_por 
                                        if pd.isna(factura.fecha_ingreso):
                                            fecha_ingreso = None
                                        else:
                                            fecha_ingreso = factura.fecha_ingreso.to_pydatetime()
                                        sistema = nc.sistema 
                                        fkCAI = nc.fkCAI 
                                        InicioCAI = 1
                                        opcion = 3

                                        Session = sessionmaker(bind=engine_destination)
                                        session = Session()
                                        
                                        try:
                                            session.execute(
                                                    "CALL SZ_INSERT_INICIO_CAI_LOCAL(:opcion, :numero, :usuario, :fecha, :sistema, :cai, :inicio)", 
                                                    {
                                                        'opcion': opcion, 
                                                        'numero': numero, 
                                                        'usuario': ingresado_por, 
                                                        'fecha': fecha_ingreso, 
                                                        'sistema': sistema, 
                                                        'cai': fkCAI, 
                                                        'inicio': InicioCAI
                                                    }
                                                )
                                            session.commit()
                                        except SQLAlchemyError as e:
                                            session.rollback()
                                            print("Error durante la inserción de notas credito:", str(e))
                                        except Exception as e:
                                            session.rollback()
                                            print("Error inesperado:", str(e))
                                        finally:
                                            session.close()


                                if not nd_ingresadas.empty:
                                    for nd in nd_ingresadas.itertuples():
                                        numero = nd.numero_nota 
                                        ingresado_por = nd.ingresado_por 
                                        if pd.isna(factura.fecha_ingreso):
                                            fecha_ingreso = None
                                        else:
                                            fecha_ingreso = factura.fecha_ingreso.to_pydatetime()
                                        sistema = nd.sistema 
                                        fkCAI = nd.fkCAI 
                                        InicioCAI = 1
                                        opcion = 2

                                        Session = sessionmaker(bind=engine_destination)
                                        session = Session()
                                        
                                        try:
                                            session.execute(
                                                    "CALL SZ_INSERT_INICIO_CAI_LOCAL(:opcion, :numero, :usuario, :fecha, :sistema, :cai, :inicio)", 
                                                    {
                                                        'opcion': opcion, 
                                                        'numero': numero, 
                                                        'usuario': ingresado_por, 
                                                        'fecha': fecha_ingreso, 
                                                        'sistema': sistema, 
                                                        'cai': fkCAI, 
                                                        'inicio': InicioCAI
                                                    }
                                                )
                                            session.commit()
                                        except SQLAlchemyError as e:
                                            session.rollback()
                                            print("Error durante la inserción de notas debito:", str(e))
                                        except Exception as e:
                                            session.rollback()
                                            print("Error inesperado:", str(e))
                                        finally:
                                            session.close()

                        except Exception as e:
                            print("Error Conexion de Maquina ", maquina, " ", format(str(e)))
                            error_info = {
                                "asunto": "Error Conexion de Maquina",
                                "descripcion": str(e),
                                "maquina": maquina
                            }
                            error_list.append(error_info)
                        
                        

        except Exception as e:
            print("Error Databases ", format(str(e)))
            error_info = {
                "asunto": "Error Databases Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        end_time = time.time()
        formatted_elapsed_time = "{:.2f}".format(end_time - start_time)
        print("Process Complete Elapsed Time:", formatted_elapsed_time)


        for error in error_list:
            asunto = error["asunto"]
            descripcion = error["descripcion"]
            maquina = error["maquina"]

            try:
                gsLocal = connections['global_local']
                with gsLocal.cursor() as cursor:
                    cursor.callproc("GS_INSERT_LOG_MIGRACION_DATOS_SUPER", [asunto, descripcion, maquina])
                
                gsLocal.close()
            except Exception as e:
                print("Error ", format(str(e)))

            """ try:
                gsNube = connections['global_nube']
                with gsNube.cursor() as cursor:
                    cursor.callproc("GS_INSERT_LOG_MIGRACION_DATOS_SUPER", [asunto, descripcion, maquina])
                
                gsNube.close()
            except Exception as e:
                print("Error ", format(str(e))) """

        return JsonResponse({'success': True, 'time': formatted_elapsed_time, "save": 1, "error": len(error_list)})


class UpdateDataSuperToLocal(APIView):
    def get(self, request, maquina, *args, **kwargs):

        auth_header = request.headers.get('API-Token', None)
        if auth_header:
            parts = auth_header.split()
            if auth_header != TOKEN:
                return Response({"error": "Token no válido o formato de autorización incorrecto."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"error": "No se proporcionó token de autorización."}, status=status.HTTP_401_UNAUTHORIZED)
        
        start_time_p = time.time()
        start_time = time.time()

        error_list = []

        password = '$Carba_admin*20'
        engine_source = create_engine('mysql+pymysql://root:{}@190.4.11.58/super_carbajal'.format(password))


        try:
            presentaciones_niveles = pd.read_sql('CALL SZ_GET_PRESENTACIONES_NIVELES()', con=engine_source)
        except Exception as e:
            print("Error Presentaciones Niveles Data ", format(str(e)))
            error_info = {
                "asunto": "Error Presentaciones Niveles Data",
                "descripcion": str(e),
                "maquina": "ge"
            }
            error_list.append(error_info)

        try:
            autorizacion_modo_local = pd.read_sql('CALL SZ_GET_AUTORIZACIONES_LOCALES_ALL()', con=engine_source)
        except Exception as e:
            print("Error Autorizaciones Data ", format(str(e)))
            error_info = {
                "asunto": "Error Autorizaciones Data",
                "descripcion": str(e),
                "maquina": "ge"
            }
            error_list.append(error_info)

        try:
            con_canales = pd.read_sql('CALL SZ_GET_CANALES_ALL()', con=engine_source)
        except Exception as e:
            print("Error Canales Data ", format(str(e)))
            error_info = {
                "asunto": "Error Canales Data",
                "descripcion": str(e),
                "maquina": "ge"
            }
            error_list.append(error_info)

        try:
            productos = pd.read_sql('CALL SZ_GET_ARTICULOS_ALL()', con=engine_source)
        except Exception as e:
            print("Error Productos Data ", format(str(e)))
            error_info = {
                "asunto": "Error Articulos Data",
                "descripcion": str(e),
                "maquina": "ge"
            }
            error_list.append(error_info)

        try:
            presentaciones = pd.read_sql('CALL SZ_GET_PRESENTACIONES_ALL()', con=engine_source)
        except Exception as e:
            print("Error Presentaciones Data ", format(str(e)))
            error_info = {
                "asunto": "Error Presentaciones Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            clientes = pd.read_sql('CALL SZ_GET_CLIENTES_ALL()', con=engine_source)
        except Exception as e:
            print("Error Clientes Data ", format(str(e)))
            error_info = {
                "asunto": "Error Clientes Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            cxc_notasdebito = pd.read_sql('CALL SZ_GET_CXC_NOTAS_DEBITO_ALL()', con=engine_source)
        except Exception as e:
            print("Error CxC Notas Debito Data ", format(str(e)))
            error_info = {
                "asunto": "Error CxC Notas Debito Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            cxc_notascredito = pd.read_sql('CALL SZ_GET_CXC_NOTAS_CREDITO_ALL()', con=engine_source)
        except Exception as e:
            print("Error CxC Notas Credito Data ", format(str(e)))
            error_info = {
                "asunto": "Error CxC Notas Credito Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            subgrupos = pd.read_sql('CALL SZ_GET_SUBGRUPOS_ALL()', con=engine_source)
        except Exception as e:
            print("Error Subgrupos Data ", format(str(e)))
            error_info = {
                "asunto": "Error Subgrupos Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            grupos = pd.read_sql('CALL SZ_GET_GRUPOS_ALL()', con=engine_source)
        except Exception as e:
            print("Error Grupos Data ", format(str(e)))
            error_info = {
                "asunto": "Error Grupos Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            bodegas = pd.read_sql('CALL SZ_GET_BODEGAS_ALL()', con=engine_source)
        except Exception as e:
            print("Error Bodegas Data ", format(str(e)))
            error_info = {
                "asunto": "Error Bodegas Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            empresas = pd.read_sql('CALL SZ_GET_EMPRESAS_ALL()', con=engine_source)
        except Exception as e:
            print("Error Empresas Data ", format(str(e)))
            error_info = {
                "asunto": "Error Empresas Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            sucursales = pd.read_sql('CALL SZ_GET_SUCURSALES_ALL()', con=engine_source)
        except Exception as e:
            print("Error Sucursales Data: {}".format(str(e)))
            error_info = {
                "asunto": "Error Sucursales Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            cxc = pd.read_sql('CALL SZ_GET_CUENTAS_X_COBRAR_ALL()', con=engine_source)
        except Exception as e:
            print("Error CxC Data ", format(str(e)))
            error_info = {
                "asunto": "Error CxC Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            config_basculas = pd.read_sql('CALL SZ_GET_CONF_BASCULA_ALL()', con=engine_source)
        except Exception as e:
            print("Error Config Basculas Data ", format(str(e)))
            error_info = {
                "asunto": "Error Basculas Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            config_cantidad_precios = pd.read_sql('CALL SZ_GET_CONFIG_CANTIDAD_PRECIOS_ALL()', con=engine_source)
        except Exception as e:
            print("Error Config Cantidad Precios Data ", format(str(e)))
            error_info = {
                "asunto": "Error Config Cantidad Precios Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            config_facturacion = pd.read_sql('CALL SZ_GET_CONFIG_FACTURACION_ALL()', con=engine_source)
        except Exception as e:
            print("Error Config Facturacion ", format(str(e)))
            error_info = {
                "asunto": "Error Config Facturacion Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            config_impresoras = pd.read_sql('CALL SZ_GET_CONFIG_IMPRESORAS_ALL()', con=engine_source)
        except Exception as e:
            print("Error Config Impresoras ", format(str(e)))
            error_info = {
                "asunto": "Error Config Impresoras Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            config_maquinas = pd.read_sql('CALL SZ_GET_CONFIG_MAQUINAS()', con=engine_source)
        except Exception as e:
            print("Error Config Maquinas ", format(str(e)))
            error_info = {
                "asunto": "Error Config Maquinas Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            cobros = pd.read_sql('CALL SZ_GET_COBROS_ALL()', con=engine_source)
        except Exception as e:
            print("Error Cobros ", format(str(e)))
            error_info = {
                "asunto": "Error Cobros Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            cobros_detalle = pd.read_sql('CALL SZ_GET_COBROS_DETALLE()', con=engine_source)
        except Exception as e:
            print("Error Cobros Detalle ", format(str(e)))
            error_info = {
                "asunto": "Error Cobros Detalle Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            cobros_formas_pago = pd.read_sql('CALL SZ_GET_COBROS_FORMAS_PAGO_ALL()', con=engine_source)
        except Exception as e:
            print("Error Cobros Formas Pago ", format(str(e)))
            error_info = {
                "asunto": "Error Cobros Formas Pago Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            medidas = pd.read_sql('CALL SZ_GET_MEDIDAS_ALL()', con=engine_source)
        except Exception as e:
            print("Error Medidas Data ", format(str(e)))
            error_info = {
                "asunto": "Error Medidas Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            tablasregistros = pd.read_sql('CALL SZ_GET_FIRMAS_AUTORIZADAS_ALL()', con=engine_source)
        except Exception as e:
            print("Error Tablas Registros Data ", format(str(e)))
            error_info = {
                "asunto": "Error Tablas Registros Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            rutas_zonas = pd.read_sql('CALL SZ_GET_RUTAS_ZONAS()', con=engine_source)
        except Exception as e:
            print("Error Rutas Zonas Data ", format(str(e)))
            error_info = {
                "asunto": "Error Rutas Zonas Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            rutas_lugares = pd.read_sql('CALL SZ_GET_RUTAS_LUGARES()', con=engine_source)
        except Exception as e:
            print("Error Rutas Lugares Data ", format(str(e)))
            error_info = {
                "asunto": "Error Rutas Lugares Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            notas = pd.read_sql('CALL SZ_GET_NOTAS_X_TABLE()', con=engine_source)
        except Exception as e:
            print("Error Notas Data ", format(str(e)))
            error_info = {
                "asunto": "Error Notas Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            caja_turnos = pd.read_sql('CALL SZ_GET_CAJAS_TURNOS_ALL()', con=engine_source)
        except Exception as e:
            print("Error Cajas Turnos Data ", format(str(e)))
            error_info = {
                "asunto": "Error Cajas Turnos Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            caja_movimientos = pd.read_sql('CALL SZ_GET_CAJAS_MOVIMIENTOS_DAY()', con=engine_source)
        except Exception as e:
            print("Error Cajas Movimientos Data ", format(str(e)))
            error_info = {
                "asunto": "Error Cajas Movimientos Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)


        try:
            control_disponibilidad = pd.read_sql('CALL SZ_GET_CONTROL_DISPONIBILIDAD()', con=engine_source)
        except Exception as e:
            print("Error Control Disponibilidad Data ", format(str(e)))
            error_info = {
                "asunto": "Error Control Disponibilidad Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        try:
            catalogo_cuentas = pd.read_sql('CALL SZ_GET_CATALOGO_CUENTAS()', con=engine_source)
        except Exception as e:
            print("Error Control Disponibilidad Data ", format(str(e)))
            error_info = {
                "asunto": "Error Control Disponibilidad Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)



        end_time_p = time.time()
        formatted_elapsed_time_p = "{:.2f}".format(end_time_p - start_time_p)
        print("Get Data Elapsed Time:", formatted_elapsed_time_p)

        try:
            superNube = connections['super']
            with superNube.cursor() as cursor:  
                cursor.callproc("SZ_GET_MAQUINAS_DATA_ALL", [maquina])
                column_names = [desc[0] for desc in cursor.description]
                databases = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]

                if databases:
                    for db in databases:
                        try:
                            PKconfig = db['PKconfig']
                            maquina = db['Maquina']
                            password = quote_plus(db['m_password'])
                            bodega = db['m_bodega']
                            engine_destination_str = 'mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=latin1'.format(
                                user=db['m_user'],
                                password=password,
                                host=db['m_host'],
                                port=db['m_port'],
                                database=db['m_database']
                            )
                            engine_destination = create_engine(engine_destination_str)


                            Session = sessionmaker(bind=engine_destination)
                            session = Session()
                            local = 0
                            
                            try:
                                sql = text("CALL SZ_GET_STATUS_MAQUINA_LOCAL(:param)")
                                result = session.execute(sql, {'param': db['PKconfig']})
                                local = result.fetchone()[0] if result.returns_rows else None
                                session.commit()

                                if local == 1:
                                    local_mode = 'LOCAL'
                                    descripcion_text = 'DEBE SUBIR DATOS Y CAMBIAR A MODO SERVIDOR'
                                else:
                                    local_mode = 'SERVIDOR'
                                    descripcion_text = 'FUNCIONANDO CORRECTAMENTE'

                                #print("Conexion a Maquina ", maquina, " en Modo ", local_mode)
                            except SQLAlchemyError as e:
                                print("Error en Conexion de Maquina ", maquina)
                                local == 3
                            finally:
                                session.close() 

                            if local == 0:
                                with engine_destination.connect() as conn:
                                    transaction = conn.begin()
                                    try:
                                        tables = [
                                            "con_canales", "articulos", "presentaciones", "clientes", 
                                            "subgrupos", "grupos", "bodegas", "empresas", "sucursales",
                                            "cuentasxcobrar", "configuracion_bascula", "configuracion_cantidad_precios",
                                            "configuracion_facturacion", "configuracion_impresoras", "configuracion_maquinas",
                                            "cobros", "cobrosdetalle", "cobrosformaspago", "medidas", "cxc_notascredito",
                                            "cxc_notasdebito", "articulos_bodega", "autorizacion_modo_local", "tablasregistros",
                                            "rutas_lugares", "rutas_zonas", "notas", "caja_turnos", "caja_movimientos",
                                            "control_disponibilidad", "catalogo_cuentas", "presentaciones_niveles"
                                        ]
                                        # Ejecutar TRUNCATE para cada tabla utilizando format()
                                        for table in tables:
                                            conn.execute(text("TRUNCATE TABLE {}".format(table)))
                                        transaction.commit()
                                    except Exception as e:
                                        print("Error en TRUNCATE TABLES", str(e))
                                        error_info = {
                                            "asunto": "Error en TRUNCATE TABLES",
                                            "descripcion": str(e),
                                            "maquina": maquina
                                        }
                                        error_list.append(error_info)

                                time.sleep(2)

                                try:
                                    presentaciones_niveles.to_sql('presentaciones_niveles', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos Presentaciones Niveles Modo Local", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos Presentaciones Niveles Modo Local",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)

                                try:
                                    catalogo_cuentas.to_sql('catalogo_cuentas', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos Catalogo Cuentas Modo Local", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos Catalogo Cuentas Modo Local",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)

                                try:
                                    control_disponibilidad.to_sql('control_disponibilidad', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos Control Disponibilidad Modo Local", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos Control Disponibilidad Modo Local",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)

                                try:
                                    caja_movimientos.to_sql('caja_movimientos', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos Cajas Movimientos Modo Local", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos Cajas Movimientos Modo Local",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)

                                try:
                                    caja_turnos.to_sql('caja_turnos', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos Cajas Turnos Modo Local", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos Cajas Turnos Modo Local",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)

                                try:
                                    notas.to_sql('notas', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Notas Modo Local", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Notas Modo Local",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)

                                try:
                                    rutas_lugares.to_sql('rutas_lugares', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Rutas Lugares Modo Local", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Rutas Lugares Modo Local",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)

                                try:
                                    rutas_zonas.to_sql('rutas_zonas', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Rutas Zonas Modo Local", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Rutas Zonas Modo Local",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)


                                try:
                                    tablasregistros.to_sql('tablasregistros', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Tablas Registros Modo Local", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Tablas Registros Modo Local",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)

                                try:
                                    autorizacion_modo_local.to_sql('autorizacion_modo_local', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Autorizaciones Modo Local", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Autorizaciones Modo Local",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)

                                try:
                                    con_canales.to_sql('con_canales', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Canales", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Canales",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)

                                try:
                                    productos.to_sql('articulos', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Articulos", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Articulos",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)
                                    
                                try:
                                    presentaciones.to_sql('presentaciones', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Presentaciones ", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Presentaciones",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)
                                    
                                try:
                                    clientes.to_sql('clientes', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Clientes ", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Clientes",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)

                                try:
                                    cxc_notascredito.to_sql('cxc_notascredito', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en CxC Notas Credito ", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en CxC Notas Credito",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)

                                try:
                                    cxc_notasdebito.to_sql('cxc_notasdebito', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en CxC Notas Debito ", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en CxC Notas Debito",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)

                                try:
                                    medidas.to_sql('medidas', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Medidas", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Medidas",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)
                                    
                                try:
                                    subgrupos.to_sql('subgrupos', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Subgrupos ", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Subgrupos",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)
                                    
                                try:
                                    grupos.to_sql('grupos', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Grupos ", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Grupos",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)
                                    
                                try:
                                    bodegas.to_sql('bodegas', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Bodegas: {}".format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Bodegas",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)
                                    
                                try:
                                    empresas.to_sql('empresas', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Empresas: {}".format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Empresas",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)
                                    
                                try:
                                    sucursales.to_sql('sucursales', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Sucursales ", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Sucursales",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)
                                    
                                try:
                                    cxc.to_sql('cuentasxcobrar', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en CxC ", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en CxC",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)
                                    
                                try:
                                    config_basculas.to_sql('configuracion_bascula', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Config Bascula ", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Config Bascula",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)
                                    
                                try:
                                    config_cantidad_precios.to_sql('configuracion_cantidad_precios', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Config Cantidad Precios ", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Config Cantidad Precios",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)
                                    
                                try:
                                    config_facturacion.to_sql('configuracion_facturacion', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Config Facturacion ", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Config Facturacion",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)
                                    
                                try:
                                    config_impresoras.to_sql('configuracion_impresoras', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Config Impresoras ", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Config Impresoras",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)

                                try:
                                    config_maquinas.to_sql('configuracion_maquinas', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Config Maquinas ", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Config Maquinas",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)
                                    
                                try:
                                    cobros.to_sql('cobros', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Cobros ", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Cobros",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)
                                    
                                try:
                                    cobros_detalle.to_sql('cobrosdetalle', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Cobros Detalle ", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Cobros Detalle",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)
                                    
                                try:
                                    cobros_formas_pago.to_sql('cobrosformaspago', engine_destination, index=False, if_exists='append', chunksize=1000)
                                except Exception as e:
                                    print("Error al insertar datos en Cobros Formas Pago ", format(str(e)))
                                    error_info = {
                                        "asunto": "Error al insertar datos en Cobros Formas Pago",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)
                                    



                                Session = sessionmaker(bind=engine_destination)
                                session = Session()

                                try:
                                    sql = text("CALL SZ_UPDATE_TRANSFERIDO()")
                                    session.execute(sql)
                                    session.commit()
                                    print("Update Campo Transferido.")
                                except Exception as e:
                                    session.rollback()
                                    print("Error Update Campo Transferido: ", str(e))
                                    error_info = {
                                        "asunto": "Error Update Campo Transferido",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)

                                try:
                                    sql = text("CALL SZ_UPDATE_CONFIGURACION_BODEGA(:bodega)")
                                    session.execute(sql, {'bodega': bodega})
                                    session.commit()
                                    print("Update Configuracion Bodega.")
                                except SQLAlchemyError as e:
                                    print("Error en Update Configuracion Bodega ", maquina)
                                    error_info = {
                                        "asunto": "Error en Update Configuracion Bodega",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)

                                try:
                                    sql = text("CALL mySP_Update_reiniciar_bodega(:bodega, :hacer, :estado, :todos, :user)")
                                    session.execute(sql, {
                                        'bodega': bodega,
                                        'hacer': 2,
                                        'estado': 2,
                                        'todos': 1,
                                        'user': 'DAC',
                                        })
                                    session.commit()
                                    print("Update Reiniciar Bodega.")
                                except SQLAlchemyError as e:
                                    print("Error en Reiniciar Bodega ", maquina)
                                    error_info = {
                                        "asunto": "Error en Reiniciar Bodega",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)
                                finally:
                                    session.close() 

                        except Exception as e:
                            print("Error Conexion de Maquina ", maquina, " ", format(str(e)))
                            error_info = {
                                "asunto": "Error Conexion de Maquina",
                                "descripcion": str(e),
                                "maquina": maquina
                            }
                            error_list.append(error_info)
                        
                        

        except Exception as e:
            print("Error Databases ", format(str(e)))
            error_info = {
                "asunto": "Error Databases Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        end_time = time.time()
        formatted_elapsed_time = "{:.2f}".format(end_time - start_time)
        print("Process Complete Elapsed Time:", formatted_elapsed_time)


        for error in error_list:
            asunto = error["asunto"]
            descripcion = error["descripcion"]
            maquina = error["maquina"]

            try:
                gsLocal = connections['global_local']
                with gsLocal.cursor() as cursor:
                    cursor.callproc("GS_INSERT_LOG_MIGRACION_DATOS_SUPER", [asunto, descripcion, maquina])
                
                gsLocal.close()
            except Exception as e:
                print("Error ", format(str(e)))

            try:
                gsNube = connections['global_nube']
                with gsNube.cursor() as cursor:
                    cursor.callproc("GS_INSERT_LOG_MIGRACION_DATOS_SUPER", [asunto, descripcion, maquina])
                
                gsNube.close()
            except Exception as e:
                print("Error ", format(str(e)))

        return JsonResponse({'success': True, 'time': formatted_elapsed_time, "error": len(error_list)})


class UpdateEstructuraSuperToLocal(APIView):
    def post(self, request, *args, **kwargs):

        auth_header = request.headers.get('API-Token', None)
        if auth_header:
            parts = auth_header.split()
            if auth_header != TOKEN:
                return Response({"error": "Token no válido o formato de autorización incorrecto."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"error": "No se proporcionó token de autorización."}, status=status.HTTP_401_UNAUTHORIZED)
        
        start_time_p = time.time()
        start_time = time.time()

        error_list = []
        maquina = 0

        sql_query = request.data.get('query')
        opcion_bd = request.data.get('opcion_bd')

        try:
            superNube = connections['super']
            with superNube.cursor() as cursor:  
                cursor.callproc("SZ_GET_MAQUINAS_DATA_ALL", [maquina])
                column_names = [desc[0] for desc in cursor.description]
                databases = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]

                if databases:
                    for db in databases:
                        try:
                            maquina = db['Maquina']
                            password = quote_plus(db['m_password'])
                            bodega = db['m_bodega']

                            if opcion_bd == '1':
                                bd_name = db['m_database']
                            else:
                                bd_name = db['m_database_seguridad']

                            engine_destination_str = 'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'.format(
                                user=db['m_user'],
                                password=password,
                                host=db['m_host'],
                                port=db['m_port'],
                                database=bd_name
                            )
                            engine_destination = create_engine(engine_destination_str)


                            with engine_destination.connect() as connection:
                                try:
                                    cursor = connection.connection.cursor()
                                    cursor.execute(sql_query)
                                    cursor.close()

                                except Exception as e:
                                    print("Error al Actualizar Estructura:", str(e))
                                    error_info = {
                                        "asunto": "Error al Actualizar Estructura",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)
                                finally:
                                    connection.close()

                        except Exception as e:
                            print("Error Conexion de Maquina ", maquina, " ", format(str(e)))
                            error_info = {
                                "asunto": "Error Conexion de Maquina al actualizar Estructura",
                                "descripcion": str(e),
                                "maquina": maquina
                            }
                            error_list.append(error_info)
                        
                        

        except Exception as e:
            print("Error Databases ", format(str(e)))
            error_info = {
                "asunto": "Error Databases Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        end_time = time.time()
        formatted_elapsed_time = "{:.2f}".format(end_time - start_time)
        print("Process Complete Elapsed Time:", formatted_elapsed_time)


        for error in error_list:
            asunto = error["asunto"]
            descripcion = error["descripcion"]
            maquina = error["maquina"]

            try:
                gsLocal = connections['global_local']
                with gsLocal.cursor() as cursor:
                    cursor.callproc("GS_INSERT_LOG_MIGRACION_DATOS_SUPER", [asunto, descripcion, maquina])
                
                gsLocal.close()
            except Exception as e:
                print("Error ", format(str(e)))

            try:
                gsNube = connections['global_nube']
                with gsNube.cursor() as cursor:
                    cursor.callproc("GS_INSERT_LOG_MIGRACION_DATOS_SUPER", [asunto, descripcion, maquina])
                
                gsNube.close()
            except Exception as e:
                print("Error ", format(str(e)))

        return JsonResponse({'success': True, 'time': formatted_elapsed_time, "error": len(error_list), 'query': sql_query})


class SyncIngresosPendientesToBank(APIView):
    def get(self, request, *args, **kwargs):

        auth_header = request.headers.get('API-Token', None)
        if auth_header:
            parts = auth_header.split()
            if auth_header != TOKEN:
                return Response({"error": "Token no válido o formato de autorización incorrecto."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"error": "No se proporcionó token de autorización."}, status=status.HTTP_401_UNAUTHORIZED)
        
        start_time_p = time.time()
        start_time = time.time()

        error_list = []

        try:
            superNubeConn = connections['super']
            with superNubeConn.cursor() as cursor:
                cursor.callproc("API_GET_INGRESOS_PENDIENTES_ALL")
                column_names = [desc[0] for desc in cursor.description]
                ingresosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
            
            
            superNubeConn.close()
        except Exception as e:
                print("Error ", format(str(e)))
                error_info = {
                    "asunto": "Error Ingresos Pendientes",
                    "descripcion": str(e),
                    "maquina": "N/A"
                }
                error_list.append(error_info)


        for ingreso in ingresosData:
            id_factura = ingreso["id_factura"]
            id_factura_sistemas = ingreso["Id_Factura_Sistemas"]
            numero_factura = ingreso["numero_factura"]
            id_orden_de_pedido = ingreso["id_orden_de_pedido"]
            id_proveedor = ingreso["id_proveedor"]
            fecha_factura = ingreso["fecha_factura"]
            fecha_plazo = ingreso["fecha_plazo"]
            total_factura = ingreso["TotalFactura"]
            saldo = ingreso["saldo"]
            fkSistema = ingreso["FkSistema"]
            fkEmpresa = ingreso["FkEmpresa"]
            valor_nota_debito = ingreso["ValorNotaDebito"]
            valor_nota_credito = ingreso["ValorNotaCredito"]

            try:
                bankConn = connections['bankConn']
                with bankConn.cursor() as cursor:
                    cursor.callproc("SP_Insert_Ingresos_Pendientes_pm", [
                            id_factura_sistemas, 
                            numero_factura, 
                            id_orden_de_pedido,
                            id_proveedor,
                            fecha_factura,
                            fecha_plazo,
                            saldo,
                            fkSistema,
                            fkEmpresa
                        ])
                bankConn.close()

                save = 1
            except Exception as e:
                save = 0
                print("Error ", format(str(e)))
                error_info = {
                    "asunto": "Error al Insertar Ingreso Pendiente",
                    "descripcion": str(e),
                    "maquina": "N/A"
                }
                error_list.append(error_info)


            if save == 1:
                try:
                    superNubeConn = connections['super']
                    with superNubeConn.cursor() as cursor:
                        cursor.callproc("API_UPDATE_INGRESOS_PENDIENTES_TRANSFERIDO", [id_factura])
                
                    superNubeConn.close()
                except Exception as e:
                    print("Error ", format(str(e)))
                    error_info = {
                        "asunto": "Error al Marcar como Transferido el Ingreso Pendiente",
                        "descripcion": str(e),
                        "maquina": "N/A"
                    }
                    error_list.append(error_info)


        end_time = time.time()
        formatted_elapsed_time = "{:.2f}".format(end_time - start_time)
        print("Process Complete Elapsed Time:", formatted_elapsed_time)


        for error in error_list:
            asunto = error["asunto"]
            descripcion = error["descripcion"]
            maquina = error["maquina"]

            try:
                gsLocal = connections['global_local']
                with gsLocal.cursor() as cursor:
                    cursor.callproc("GS_INSERT_LOG_MIGRACION_DATOS_SUPER", [asunto, descripcion, maquina])
                
                gsLocal.close()
            except Exception as e:
                print("Error ", format(str(e)))

            try:
                gsNube = connections['global_nube']
                with gsNube.cursor() as cursor:
                    cursor.callproc("GS_INSERT_LOG_MIGRACION_DATOS_SUPER", [asunto, descripcion, maquina])
                
                gsNube.close()
            except Exception as e:
                print("Error ", format(str(e)))

        return JsonResponse({'success': True, 'time': formatted_elapsed_time})


class UpdateDataGlobalToLocal(APIView):
    def get(self, request, maquina, *args, **kwargs):

        auth_header = request.headers.get('API-Token', None)
        if auth_header:
            parts = auth_header.split()
            if auth_header != TOKEN:
                return Response({"error": "Token no válido o formato de autorización incorrecto."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"error": "No se proporcionó token de autorización."}, status=status.HTTP_401_UNAUTHORIZED)
        
        start_time_p = time.time()
        start_time = time.time()

        error_list = []

        password = '$Carba_admin*20'
        engine_source = create_engine('mysql+pymysql://root:{}@190.4.11.58/global_security'.format(password))



        try:
            adminIT = pd.read_sql('CALL SZ_GET_ADMIN_IT_ALL()', con=engine_source)
        except Exception as e:
            print("Error Admin IT Data ", format(str(e)))
            error_info = {
                "asunto": "Error Admin IT Data",
                "descripcion": str(e),
                "maquina": "ge"
            }
            error_list.append(error_info)

        # ============================================================================

        try:
            grupos = pd.read_sql('CALL SZ_GET_GRUPOS_SUPER_ALL()', con=engine_source)
        except Exception as e:
            print("Error Grupos Data ", format(str(e)))
            error_info = {
                "asunto": "Error Grupos Data",
                "descripcion": str(e),
                "maquina": "ge"
            }
            error_list.append(error_info)

        try:
            usuarios_grupo = pd.read_sql('CALL SZ_GET_USUARIOS_GRUPOS_SUPER_ALL()', con=engine_source)
        except Exception as e:
            print("Error Grupos Caja Data ", format(str(e)))
            error_info = {
                "asunto": "Error Grupos Caja Data",
                "descripcion": str(e),
                "maquina": "ge"
            }
            error_list.append(error_info)

        # ============================================================================

        try:
            menus = pd.read_sql('CALL SZ_GET_MENUS_SUPER_ALL()', con=engine_source)
        except Exception as e:
            print("Error Menus Data ", format(str(e)))
            error_info = {
                "asunto": "Error Menus Data",
                "descripcion": str(e),
                "maquina": "ge"
            }
            error_list.append(error_info)

        try:
            menus_grupo = pd.read_sql('CALL SZ_GET_MENUS_GRUPO_SUPER_ALL()', con=engine_source)
        except Exception as e:
            print("Error Menus Grupos Data ", format(str(e)))
            error_info = {
                "asunto": "Error Menus Grupos Data",
                "descripcion": str(e),
                "maquina": "ge"
            }
            error_list.append(error_info)

        # ============================================================================

        try:
            usuarios = pd.read_sql('CALL SZ_GET_ALL_USERS()', con=engine_source)
        except Exception as e:
            print("Error Usuarios Data ", format(str(e)))
            error_info = {
                "asunto": "Error Usuarios Data",
                "descripcion": str(e),
                "maquina": "ge"
            }
            error_list.append(error_info)

        # ============================================================================

        try:
            usuarios_modulo = pd.read_sql('CALL SZ_GET_USUARIOS_MODULOS_SUPER_ALL()', con=engine_source)
        except Exception as e:
            print("Error Usuarios Modulos Data ", format(str(e)))
            error_info = {
                "asunto": "Error Usuarios Modulos Data",
                "descripcion": str(e),
                "maquina": "ge"
            }
            error_list.append(error_info)

        # ============================================================================

        try:
            usuarios_sucursales = pd.read_sql('CALL SZ_GET_USUARIOS_SUCURSALES_ALL()', con=engine_source)
        except Exception as e:
            print("Error Usuarios Sucursales Data ", format(str(e)))
            error_info = {
                "asunto": "Error Usuarios Sucursales Data",
                "descripcion": str(e),
                "maquina": "ge"
            }
            error_list.append(error_info)



        end_time_p = time.time()
        formatted_elapsed_time_p = "{:.2f}".format(end_time_p - start_time_p)
        print("Get Data Elapsed Time:", formatted_elapsed_time_p)

        try:
            superNube = connections['super']
            with superNube.cursor() as cursor:  
                cursor.callproc("SZ_GET_MAQUINAS_DATA_ALL", [maquina])
                column_names = [desc[0] for desc in cursor.description]
                databases = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]

                if databases:
                    for db in databases:
                        try:
                            maquina = db['Maquina']
                            password = quote_plus(db['m_password'])
                            bodega = db['m_bodega']
                            engine_destination_str = 'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'.format(
                                user=db['m_user'],
                                password=password,
                                host=db['m_host'],
                                port=db['m_port'],
                                database=db['m_database_seguridad']
                            )
                            engine_destination = create_engine(engine_destination_str)

                            with engine_destination.connect() as conn:
                                transaction = conn.begin()  # Inicia una transacción si tus consultas deben ser atómicas
                                try:
                                    conn.execute("TRUNCATE TABLE usuarios_admin_it;")
                                    conn.execute("TRUNCATE TABLE usuarios_grupo;")
                                    conn.execute("TRUNCATE TABLE grupos;")
                                    conn.execute("TRUNCATE TABLE menus;")
                                    conn.execute("TRUNCATE TABLE menus_grupo;")
                                    conn.execute("TRUNCATE TABLE usuarios;")
                                    conn.execute("TRUNCATE TABLE usuarios_modulo;")
                                    conn.execute("TRUNCATE TABLE usuarios_sucursales;")
                                    
                                    transaction.commit()
                                except Exception as e:
                                    print("Error en TRUNCATE TABLES", str(e))
                                    error_info = {
                                        "asunto": "Error en TRUNCATE TABLES",
                                        "descripcion": str(e),
                                        "maquina": maquina
                                    }
                                    error_list.append(error_info)

                            try:
                                adminIT.to_sql('usuarios_admin_it', engine_destination, index=False, if_exists='append', chunksize=1000)
                            except Exception as e:
                                print("Error al insertar datos en Usuarios Admin IT", format(str(e)))
                                error_info = {
                                    "asunto": "Error al insertar datos en Usuarios Admin IT",
                                    "descripcion": str(e),
                                    "maquina": maquina
                                }
                                error_list.append(error_info)
                            
                            # ============================================================================

                            try:
                                usuarios_grupo.to_sql('usuarios_grupo', engine_destination, index=False, if_exists='append', chunksize=1000)
                            except Exception as e:
                                print("Error al insertar datos en Usuarios Grupos", format(str(e)))
                                error_info = {
                                    "asunto": "Error al insertar datos en Usuarios Grupos",
                                    "descripcion": str(e),
                                    "maquina": maquina
                                }
                                error_list.append(error_info)

                            try:
                                grupos.to_sql('grupos', engine_destination, index=False, if_exists='append', chunksize=1000)
                            except Exception as e:
                                print("Error al insertar datos en Grupos", format(str(e)))
                                error_info = {
                                    "asunto": "Error al insertar datos en Grupos",
                                    "descripcion": str(e),
                                    "maquina": maquina
                                }
                                error_list.append(error_info)

                            # ============================================================================

                            try:
                                menus.to_sql('menus', engine_destination, index=False, if_exists='append', chunksize=1000)
                            except Exception as e:
                                print("Error al insertar datos en Menus", format(str(e)))
                                error_info = {
                                    "asunto": "Error al insertar datos en Menus",
                                    "descripcion": str(e),
                                    "maquina": maquina
                                }
                                error_list.append(error_info)
                                
                            try:
                                menus_grupo.to_sql('menus_grupo', engine_destination, index=False, if_exists='append', chunksize=1000)
                            except Exception as e:
                                print("Error al insertar datos en Menus Grupos", format(str(e)))
                                error_info = {
                                    "asunto": "Error al insertar datos en Menus Grupos",
                                    "descripcion": str(e),
                                    "maquina": maquina
                                }
                                error_list.append(error_info)

                                
                            # ============================================================================
                            
                            try:
                                usuarios.to_sql('usuarios', engine_destination, index=False, if_exists='append', chunksize=1000)
                            except Exception as e:
                                print("Error al insertar datos en Usuarios", format(str(e)))
                                error_info = {
                                    "asunto": "Error al insertar datos en Usuarios",
                                    "descripcion": str(e),
                                    "maquina": maquina
                                }
                                error_list.append(error_info)
                                
                            # ============================================================================
                            
                            try:
                                usuarios_modulo.to_sql('usuarios_modulo', engine_destination, index=False, if_exists='append', chunksize=1000)
                            except Exception as e:
                                print("Error al insertar datos en Usuarios Modulo", format(str(e)))
                                error_info = {
                                    "asunto": "Error al insertar datos en Usuarios Modulo",
                                    "descripcion": str(e),
                                    "maquina": maquina
                                }
                                error_list.append(error_info)
                            
                                
                            # ============================================================================
                            
                            try:
                                usuarios_sucursales.to_sql('usuarios_sucursales', engine_destination, index=False, if_exists='append', chunksize=1000)
                            except Exception as e:
                                print("Error al insertar datos en Usuarios Sucursales", format(str(e)))
                                error_info = {
                                    "asunto": "Error al insertar datos en Usuarios Sucursales",
                                    "descripcion": str(e),
                                    "maquina": maquina
                                }
                                error_list.append(error_info)
                            
                                

                        except Exception as e:
                            print("Error Conexion de Maquina ", maquina, " ", format(str(e)))
                            error_info = {
                                "asunto": "Error Conexion de Maquina",
                                "descripcion": str(e),
                                "maquina": maquina
                            }
                            error_list.append(error_info)
                        
                        

        except Exception as e:
            print("Error Databases ", format(str(e)))
            error_info = {
                "asunto": "Error Databases Data",
                "descripcion": str(e),
                "maquina": "GET DATA"
            }
            error_list.append(error_info)

        end_time = time.time()
        formatted_elapsed_time = "{:.2f}".format(end_time - start_time)
        print("Process Complete Elapsed Time:", formatted_elapsed_time)


        for error in error_list:
            asunto = error["asunto"]
            descripcion = error["descripcion"]
            maquina = error["maquina"]

            try:
                gsLocal = connections['global_local']
                with gsLocal.cursor() as cursor:
                    cursor.callproc("GS_INSERT_LOG_MIGRACION_DATOS_SUPER", [asunto, descripcion, maquina])
                
                gsLocal.close()
            except Exception as e:
                print("Error ", format(str(e)))

            try:
                gsNube = connections['global_nube']
                with gsNube.cursor() as cursor:
                    cursor.callproc("GS_INSERT_LOG_MIGRACION_DATOS_SUPER", [asunto, descripcion, maquina])
                
                gsNube.close()
            except Exception as e:
                print("Error ", format(str(e)))

        return JsonResponse({'success': True, 'time': formatted_elapsed_time, "error": len(error_list)})


class GetDisponibilidadCajaSupermercado(APIView):
    def get(self, request, *args, **kwargs):

        auth_header = request.headers.get('API-Token', None)
        if auth_header:
            parts = auth_header.split()
            if auth_header != TOKEN:
                return Response({"error": "Token no válido o formato de autorización incorrecto."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"error": "No se proporcionó token de autorización."}, status=status.HTTP_401_UNAUTHORIZED)
        
        start_time_p = time.time()
        start_time = time.time()

        json_list = []

        maquina = 0

        try:
            superNube = connections['super']
            with superNube.cursor() as cursor:  
                cursor.callproc("SZ_GET_MAQUINAS_DATA_ALL", [maquina])
                column_names = [desc[0] for desc in cursor.description]
                databases = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]

                if databases:
                    for db in databases:
                        try:
                            PKconfig = db['PKconfig']
                            maquina = db['Maquina']
                            password = quote_plus(db['m_password'])
                            bodega = db['m_bodega']
                            engine_destination_str = 'mysql+pymysql://{user}:{password}@{host}:{port}/{database}'.format(
                                user=db['m_user'],
                                password=password,
                                host=db['m_host'],
                                port=db['m_port'],
                                database=db['m_database']
                            )
                            engine_destination = create_engine(engine_destination_str)

                            Session = sessionmaker(bind=engine_destination)
                            session = Session()

                            
                            try:
                                sql = text("CALL SZ_GET_STATUS_MAQUINA_LOCAL(:param)")
                                result = session.execute(sql, {'param': PKconfig})
                                local = result.fetchone()[0] if result.returns_rows else None
                                session.commit()

                                if local == 1:
                                    local_mode = 'LOCAL'
                                    descripcion_text = 'DEBE SUBIR DATOS Y CAMBIAR A MODO SERVIDOR'
                                else:
                                    local_mode = 'SERVIDOR'
                                    descripcion_text = 'FUNCIONANDO CORRECTAMENTE'

                                print("Conexion a Maquina ", maquina, " en Modo ", local_mode)
                                success_text = "Conexion a Maquina {} en Modo {}".format(maquina, local_mode)
                                json_info = {
                                    "asunto": success_text,
                                    "descripcion": descripcion_text,
                                    "maquina": maquina,
                                    "modo": local,
                                }
                                json_list.append(json_info)
                            except SQLAlchemyError as e:
                                print("Error en Conexion de Maquina ", maquina)
                                error_text = "Error en Conexion de Maquina  {}".format(maquina)
                                json_info = {
                                    "asunto": error_text,
                                    "descripcion": "VERIFICAR ESTADO Y CONEXIONES DE LA MAQUINA",
                                    "maquina": maquina,
                                    "modo": 3,
                                }
                                json_list.append(json_info)
                            finally:
                                session.close() 


                        except Exception as e:
                            print("")
        
        except Exception as e:
            print("Error Databases ", format(str(e)))

        end_time = time.time()
        formatted_elapsed_time = "{:.2f}".format(end_time - start_time)
        print("Process Complete Elapsed Time:", formatted_elapsed_time)

        print(json_list)

        for json in json_list:
            asunto = json["asunto"]
            descripcion = json["descripcion"]
            maquina = json["maquina"]
            modo = json["modo"]

            try:
                superNube = connections['super']
                with superNube.cursor() as cursor:
                    cursor.callproc("SZ_INSERT_MODO_CONEXION_MAQUINA_LOG", [asunto, maquina, descripcion, modo])
                
                superNube.close()
            except Exception as e:
                print("Error ", format(str(e)))


        url = 'http://3.230.160.184/DAC/public/notification/conexion/maquinas/supermercado'

        try:
            response = requests.get(url)
            response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        except HTTPError as http_err:
            print("HTTPError ", format(str(http_err)))
        except Exception as err:
            print("Exception ", format(str(err)))
        else:
            print('Success!')

        return JsonResponse({'success': True, 'time': formatted_elapsed_time, "json": len(json_list)})








class TokenGenerarSolicitud(APIView):
    def post(self, request, *args, **kwargs):

        auth_header = request.headers.get('API-Token', None)
        if auth_header:
            if auth_header != TOKEN:
                return Response({"error": "Token no válido o formato de autorización incorrecto."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"error": "No se proporcionó token de autorización."}, status=status.HTTP_401_UNAUTHORIZED)
        
        
        solicitud_id = 0
        mail_error = 0

        login_url = request.build_absolute_uri(
            reverse("login")
        )

        # Verifica si los datos vienen como JSON (raw)
        if request.content_type == 'application/json':
            # Decodifica los bytes a string antes de cargar el JSON
            data = json.loads(request.body.decode('utf-8'))
        else:
            # Si no es JSON, se asume que es form-data y se obtiene de request.POST
            data = {
                'sucursal': request.POST.get('sucursal', '0'),
                'num_documento': request.POST.get('num_documento', 0),
                'id_tipo_token': request.POST.get('id_tipo_token', 0),
                'id_modulo': request.POST.get('id_modulo', 0),
                'usuario': request.POST.get('usuario', ''),
                'tabla': request.POST.get('tabla', ''),
                'assignedDetalle': json.loads(request.POST.get('assignedDetalle', '[]'))  # Convertimos el detalle a JSON
            }

        # Accede a los datos independientemente del formato
        sucursal = data.get('sucursal')
        num_documento = data.get('num_documento')
        id_tipo_token = data.get('id_tipo_token')
        id_modulo = data.get('id_modulo')
        usuario = data.get('usuario')
        tabla = data.get('tabla')
        assignedDetalle = data.get('assignedDetalle')
        existe = 0

        try:    
            with connections['universal'].cursor() as cursor:
                cursor.callproc('CTRL_INSERT_TOKEN_HEADER_SUCURSAL', [sucursal, num_documento, id_tipo_token, id_modulo, usuario])
                result = cursor.fetchall()
                cursor.nextset()  # Esto asegura que se avance al siguiente conjunto de resultados

                if result:
                    solicitud_id = result[0][0]
                    existe = result[0][1]

                    if existe == 0 or existe == '0':
                        for detalle in assignedDetalle:
                            mov_original = detalle.get('mov_original')
                            documento = detalle.get('documento')
                            cantidad = detalle.get('cantidad')
                            descripcion = detalle.get('descripcion')
                            valor = detalle.get('valor')
                            observacion = detalle.get('observacion')

                            cursor.callproc('CTRL_INSERT_TOKEN_DETAILS', [
                                solicitud_id, mov_original, documento, cantidad, descripcion, valor, observacion, tabla
                            ])
                            cursor.fetchall()
                            cursor.nextset()  

                if existe == 0 or existe == '0':
                    with connections['universal'].cursor() as cursor:
                        cursor.callproc('CTRL_SOLICITUD_CORREOS', [id_tipo_token, solicitud_id])
                        emailsQuery = cursor.fetchall()

                        if emailsQuery:
                            for emails in emailsQuery:
                                email = emails[0]
                                tipo_token = emails[1]
                                message = emails[2]

                                try:
                                    send_mail(
                                        "SOLICITUD DE TOKEN DE {} CREADA".format(tipo_token),
                                        "",
                                        settings.EMAIL_HOST_USER,
                                        [email],
                                        fail_silently=False,
                                        html_message=render_to_string(
                                            "email_template_v1.html",
                                            {
                                                "title": "SOLICITUD DE TOKEN DE {} CREADA".format(tipo_token),
                                                "message": "Buen día, por favor verifica el apartado de Autorizaciones en DAC para visualizar la siguiente solicitud {}".format(message),
                                                "token": "",
                                                "login_url": login_url,
                                                "btn_redirect": 1,
                                            },
                                        ),
                                    )
                                    mail_error = 1
                                except Exception as e:
                                    mail_error = str(e)

            datos = {'save': 1, 'mail': mail_error, 'existe': existe}
        except Exception as e:
            datos = {'save': 0, 'error': str(e), 'mail_error': mail_error}
        
        return JsonResponse(datos)


class TokenValidarExisteUnaSolicitud(APIView):
    def post(self, request, *args, **kwargs):

        auth_header = request.headers.get('API-Token', None)
        if auth_header:
            if auth_header != TOKEN:
                return Response({"error": "Token no válido o formato de autorización incorrecto."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"error": "No se proporcionó token de autorización."}, status=status.HTTP_401_UNAUTHORIZED)
        
        
        solicitud_id = 0
        mail_error = 0
        estado = 'NO EXISTE'

        login_url = request.build_absolute_uri(
            reverse("login")
        )

        # Verifica si los datos vienen como JSON (raw)
        if request.content_type == 'application/json':
            # Decodifica los bytes a string antes de cargar el JSON
            data = json.loads(request.body.decode('utf-8'))
        else:
            # Si no es JSON, se asume que es form-data y se obtiene de request.POST
            data = {
                'sucursal': request.POST.get('sucursal', '0'),
                'num_documento': request.POST.get('num_documento', 0),
                'id_tipo_token': request.POST.get('id_tipo_token', 0),
                'id_modulo': request.POST.get('id_modulo', 0),
                'usuario': request.POST.get('usuario', ''),
                'tabla': request.POST.get('tabla', ''),
                'assignedDetalle': json.loads(request.POST.get('assignedDetalle', '[]'))  # Convertimos el detalle a JSON
            }

        # Accede a los datos independientemente del formato
        sucursal = data.get('sucursal')
        num_documento = data.get('num_documento')
        id_tipo_token = data.get('id_tipo_token')
        id_modulo = data.get('id_modulo')
        usuario = data.get('usuario')
        tabla = data.get('tabla')
        assignedDetalle = data.get('assignedDetalle')
        existe = 0

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('CTRL_VALIDAR_EXISTE_SOLICITUD', [sucursal, num_documento, id_tipo_token, id_modulo, usuario])
                result = cursor.fetchall()
                cursor.nextset()  # Esto asegura que se avance al siguiente conjunto de resultados

                if result:
                    existe = result[0][0]
                    estado = result[0][1]

            datos = {'save': 1, 'existe': existe, 'estado': estado}
        except Exception as e:
            datos = {'save': 0, 'error': str(e)}
        
        return JsonResponse(datos)


class TokenCancelarSolicitud(APIView):
    def post(self, request, *args, **kwargs):

        auth_header = request.headers.get('API-Token', None)
        if auth_header:
            if auth_header != TOKEN:
                return Response({"error": "Token no válido o formato de autorización incorrecto."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"error": "No se proporcionó token de autorización."}, status=status.HTTP_401_UNAUTHORIZED)
        
        
        solicitud_id = 0
        mail_error = 0

        login_url = request.build_absolute_uri(
            reverse("login")
        )

        # Verifica si los datos vienen como JSON (raw)
        if request.content_type == 'application/json':
            # Decodifica los bytes a string antes de cargar el JSON
            data = json.loads(request.body.decode('utf-8'))
        else:
            # Si no es JSON, se asume que es form-data y se obtiene de request.POST
            data = {
                'sucursal': request.POST.get('sucursal', 0),
                'num_documento': request.POST.get('num_documento', 0),
                'id_tipo_token': request.POST.get('id_tipo_token', 0),
                'id_modulo': request.POST.get('id_modulo', 0),
                'usuario': request.POST.get('usuario', ''),
                'tabla': request.POST.get('tabla', ''),
                'comentario': request.POST.get('comentario', 'Por politicas de Validacion y Seguridad del Sistema.')
            }

        # Accede a los datos independientemente del formato
        sucursal = data.get('sucursal')
        num_documento = data.get('num_documento')
        id_tipo_token = data.get('id_tipo_token')
        id_modulo = data.get('id_modulo')
        usuario = data.get('usuario')
        tabla = data.get('tabla')
        comentario = data.get('comentario')

        try:
            with connections['universal'].cursor() as cursor:
                cursor.callproc('CTRL_SOLICITUD_CANCELAR_SUCURSAL', [sucursal, num_documento, id_tipo_token, id_modulo, usuario, comentario])
                result = cursor.fetchall()
                cursor.nextset() 

            with connections['universal'].cursor() as cursor:
                cursor.callproc('CTRL_GET_CORREO', [usuario])
                emailsQuery = cursor.fetchall()

                if emailsQuery:
                    for emails in emailsQuery:
                        email = emails[0]

                        try:
                            send_mail(
                                "SOLICITUD DE TOKEN CANCELADA",
                                "",
                                settings.EMAIL_HOST_USER,
                                [email],
                                fail_silently=False,
                                html_message=render_to_string(
                                    "email_template_v1.html",
                                    {
                                        "title": "SOLICITUD DE TOKEN CANCELADA",
                                        "message": "Buen dia, tu solicitud de token ha sido cancelada, realizaste cambios y ya no aplica la solicitud anterior. MOTIVO: {}".format(comentario),
                                        "token": "",
                                        "login_url": login_url,
                                        "btn_redirect": 0,
                                    },
                                ),
                            )
                            mail_error = 1
                        except Exception as e:
                            mail_error = str(e)

            datos = {'save': 1, 'mail': mail_error}
        except Exception as e:
            datos = {'save': 0, 'error': str(e), 'mail_error': mail_error}
        
        return JsonResponse(datos)


class TokenGetMisSolicitudes(APIView):
    def post(self, request, *args, **kwargs):

        auth_header = request.headers.get('API-Token', None)
        if auth_header:
            if auth_header != TOKEN:
                return Response({"error": "Token no válido o formato de autorización incorrecto."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"error": "No se proporcionó token de autorización."}, status=status.HTTP_401_UNAUTHORIZED)
        
        userName = request.POST.get('user_id')
        date1 = request.POST.get('date1')
        date2 = request.POST.get('date2')

        try:
            defaultConn = connections['universal']
            with defaultConn.cursor() as cursor:
                cursor.callproc('CTRL_GET_MIS_SOLICITUDES_TOKEN', [userName, date1, date2])
                column_names = [desc[0] for desc in cursor.description]
                solicitudesData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
            
            # Cierra la conexión
            defaultConn.close()
            
            # Devuelve los resultados como JSON
            return JsonResponse({'data': solicitudesData})
        except Exception as e:
            # Manejo de excepciones, puedes personalizar esto según tus necesidades
            return JsonResponse({'error': str(e)})


class TokenGetSolicitudes(APIView):
    def post(self, request, *args, **kwargs):

        auth_header = request.headers.get('API-Token', None)
        if auth_header:
            if auth_header != TOKEN:
                return Response({"error": "Token no válido o formato de autorización incorrecto."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"error": "No se proporcionó token de autorización."}, status=status.HTTP_401_UNAUTHORIZED)
        
        user_id = request.POST.get('user_id')
        opcion = request.POST.get('opcion')
        date1 = request.POST.get('date1')
        date2 = request.POST.get('date2')

        try:
            defaultConn = connections['universal']
            with defaultConn.cursor() as cursor:
                cursor.callproc('CTRL_GET_SOLICITUDES_TOKEN', [user_id, opcion, date1, date2])
                column_names = [desc[0] for desc in cursor.description]
                solicitudesData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
            
            # Cierra la conexión
            defaultConn.close()
            
            # Devuelve los resultados como JSON
            return JsonResponse({'data': solicitudesData})
        except Exception as e:
            # Manejo de excepciones, puedes personalizar esto según tus necesidades
            return JsonResponse({'error': str(e)})


class TokenGetSolicitudesDetails(APIView):
    def post(self, request, *args, **kwargs):

        auth_header = request.headers.get('API-Token', None)
        if auth_header:
            if auth_header != TOKEN:
                return Response({"error": "Token no válido o formato de autorización incorrecto."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"error": "No se proporcionó token de autorización."}, status=status.HTTP_401_UNAUTHORIZED)
        
        id_solicitud = request.POST.get('id_solicitud')

        try:
            defaultConn = connections['universal']
            with defaultConn.cursor() as cursor:
                cursor.callproc('CTRL_GET_SOLICITUDES_DETALLES_TOKEN', [id_solicitud])
                column_names = [desc[0] for desc in cursor.description]
                detallesData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
            
            # Cierra la conexión
            defaultConn.close()
            
            # Devuelve los resultados como JSON
            return JsonResponse({'data': detallesData})
        except Exception as e:
            # Manejo de excepciones, puedes personalizar esto según tus necesidades
            return JsonResponse({'error': str(e)})


class TokenRevisarDetalleSolicitud(APIView):
    def post(self, request, *args, **kwargs):

        auth_header = request.headers.get('API-Token', None)
        if auth_header:
            if auth_header != TOKEN:
                return Response({"error": "Token no válido o formato de autorización incorrecto."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"error": "No se proporcionó token de autorización."}, status=status.HTTP_401_UNAUTHORIZED)
        
        detalle_id = request.POST.get('detalle_id')
        userName = request.POST.get('userName')

        mail_error = 0
        sinRevisar = 1
        login_url = request.build_absolute_uri(
            reverse("login")
        )

        try:
            defaultConn = connections['universal']
            with defaultConn.cursor() as cursor:
                cursor.callproc('CTRL_VALIDAR_DETALLES_SOLICITUD_TOKEN', [detalle_id, userName])
                tokenQuery = cursor.fetchall()
            
                if tokenQuery:
                    title = tokenQuery[0][0]
                    message = tokenQuery[0][1]
                    token = tokenQuery[0][2]
                    email = tokenQuery[0][3]
                    sinRevisar = tokenQuery[0][4]
            
                    try:
                        send_mail(
                            "SOLICITUD DE TOKEN",
                            "",
                            settings.EMAIL_HOST_USER,
                            [email],
                            fail_silently=False,
                            html_message=render_to_string(
                                "email_template_v1.html",
                                {
                                    "title": title,
                                    "message": message,
                                    "token": token,
                                    "login_url": login_url,
                                    "btn_redirect": 0,
                                },
                            ),
                        )
                        mail_error = 1
                    except Exception as e:
                        mail_error = str(e)
                
            
            datos = {'save': 1, 'mail': mail_error, 'sinRevisar': sinRevisar}
        except Exception as e:
            datos = {'save': 0, 'error': str(e), 'mail_error': mail_error}
        
        return JsonResponse(datos)


class TokenSolicitudComentario(APIView):
    def post(self, request, *args, **kwargs):

        auth_header = request.headers.get('API-Token', None)
        if auth_header:
            if auth_header != TOKEN:
                return Response({"error": "Token no válido o formato de autorización incorrecto."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"error": "No se proporcionó token de autorización."}, status=status.HTTP_401_UNAUTHORIZED)
        
        detalle_id = request.POST.get('detalle_id')
        comentario = request.POST.get('comentario')
        opcion = request.POST.get('opcion')
        userName = request.POST.get('userName')

        mail_error = 0
        email = ''
        login_url = request.build_absolute_uri(
            reverse("login")
        )

        try:
            defaultConn = connections['universal']
            with defaultConn.cursor() as cursor:
                cursor.callproc('CTRL_SOLICITUD_TOKEN_COMENTAR_O_RECHAZAR', [detalle_id, comentario, opcion, userName])
                tokenRechazar = cursor.fetchall()
            
                if tokenRechazar:
                    title = tokenRechazar[0][0]
                    message = tokenRechazar[0][1]
                    email = tokenRechazar[0][2]
            
                if opcion == 0 or opcion == '0':
                    try:
                        send_mail(
                            "SOLICITUD DE TOKEN RECHAZADA",
                            "",
                            settings.EMAIL_HOST_USER,
                            [email],
                            fail_silently=False,
                            html_message=render_to_string(
                                "email_template_v1.html",
                                {
                                    "title": title,
                                    "message": message,
                                    "token": "",
                                    "login_url": login_url,
                                    "btn_redirect": 0,
                                },
                            ),
                        )
                        mail_error = 1
                    except Exception as e:
                        mail_error = str(e)
            
            datos = {'save': 1, 'mail': mail_error, 'email': email}
        except Exception as e:
            datos = {'save': 0, 'error': str(e)}
        
        return JsonResponse(datos)


class TokenValidar(APIView):
    def post(self, request, *args, **kwargs):

        auth_header = request.headers.get('API-Token', None)
        if auth_header:
            if auth_header != TOKEN:
                return Response({"error": "Token no válido o formato de autorización incorrecto."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"error": "No se proporcionó token de autorización."}, status=status.HTTP_401_UNAUTHORIZED)
        
        num_documento = request.POST.get('num_documento')
        usuario = request.POST.get('usuario')
        token = request.POST.get('token')
        status = 0

        try:
            defaultConn = connections['universal']
            with defaultConn.cursor() as cursor:
                cursor.callproc('CTRL_VALIDAR_TOKEN', [usuario, token, num_documento])
                tokenQuery = cursor.fetchall()
            
                if tokenQuery:
                    status = tokenQuery[0][0]
            
            datos = {'save': 1, 'status': status}
        except Exception as e:
            datos = {'save': 0, 'error': str(e), 'mail_error': mail_error}
        
        return JsonResponse(datos) 



class TokenValidar_v2(APIView):
    def post(self, request, *args, **kwargs):

        auth_header = request.headers.get('API-Token', None)
        if auth_header:
            if auth_header != TOKEN:
                return Response({"error": "Token no válido o formato de autorización incorrecto."}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({"error": "No se proporcionó token de autorización."}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Verifica si los datos vienen como JSON (raw)
        if request.content_type == 'application/json':
            # Decodifica los bytes a string antes de cargar el JSON
            data = json.loads(request.body.decode('utf-8'))
        else:
            # Si no es JSON, se asume que es form-data y se obtiene de request.POST
            data = {
                'num_documento': request.POST.get('num_documento', 0),
                'id_tipo_token': request.POST.get('id_tipo_token', 0),
                'id_modulo': request.POST.get('id_modulo', 0),
                'usuario': request.POST.get('usuario', ''),
            }

        num_documento = data.get('num_documento')
        id_tipo_token = data.get('id_tipo_token')
        id_modulo = data.get('id_modulo')
        usuario = data.get('usuario')

        try:
            defaultConn = connections['universal']
            with defaultConn.cursor() as cursor:
                cursor.callproc('CTRL_VALIDAR_TOKEN_v2', [usuario, id_tipo_token, id_modulo, num_documento])
                tokenQuery = cursor.fetchall()
            
                if tokenQuery:
                    status = tokenQuery[0][0]
            
            datos = {'save': 1, 'status': status}
        except Exception as e:
            datos = {'save': 0, 'error': str(e), 'mail_error': mail_error}
        
        return JsonResponse(datos) 






