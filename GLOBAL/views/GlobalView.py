import pdb
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.db import connections
from django.http import JsonResponse
from django.conf import settings
from datetime import datetime, timedelta
import requests
import pandas as pd
import time
import hashlib
import os
import subprocess
import traceback
from rest_framework_simplejwt.tokens import RefreshToken
import jwt
from django.views.decorators.csrf import csrf_exempt
import json
import base64
from django.shortcuts import redirect, render
from django.http import HttpResponseRedirect
import logging
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, HttpResponseRedirect
import xlrd
from datetime import date, datetime
from django.http import JsonResponse, Http404
from django.urls import reverse
import csv
import tempfile
import pyodbc
import pymssql
from django.db import transaction

def get_accesos_global_security(request):
    user_id = request.session.get('user_id', '')
    request.session['globalAdminIT'] = 0

    appConn = connections['global_nube']
    with appConn.cursor() as cursor:
        cursor.callproc('WEB_GET_ADMIN_IT', [user_id, 10])
        adminITQuery = cursor.fetchall()

        if adminITQuery:
            request.session['globalAdminIT'] = 1

        appConn.close()

def global_main(request):
    user_id = request.session.get('user_id', '')

    if user_id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        get_accesos_global_security(request)
        
        return render(request, 'global_main.html')
    

def logoutRequest(request):
    request.session.flush()

    return HttpResponseRedirect(reverse('login'))


def global_modulos_usuario(request):
    user_id = request.session.get('user_id', '')

    if user_id == '':  
        return HttpResponseRedirect(reverse('login'))
    else:
        return render(request, 'usuarios/modulos_usuario.html') 

def global_acciones_usuario(request):
    user_id = request.session.get('user_id', '')
    adminIT = request.session.get('globalAdminIT', 0)

    if user_id == '':  
        return HttpResponseRedirect(reverse('login'))
    if adminIT == 1:

            modulosData = ""
            
            try:
                udcConn = connections['global_nube']
                with udcConn.cursor() as cursor:
                    cursor.callproc("GS_GET_ALL_MODULOS")
                    column_names = [desc[0] for desc in cursor.description]
                    modulosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
                udcConn.close()
            except Exception as e:
                return JsonResponse({'error': str(e)})

            context = {
                "modulos": modulosData
            }
            
            return render(request, 'usuarios/acciones_usuario.html', context)

def global_admin_aplicaciones(request):
    user_id = request.session.get('user_id', '')
    adminIT = request.session.get('globalAdminIT', 0)

    if user_id == '':  
        return HttpResponseRedirect(reverse('login'))
    if adminIT == 1:

            modulosData = ""
            
            try:
                udcConn = connections['global_nube']
                with udcConn.cursor() as cursor:
                    cursor.callproc("GS_GET_ALL_MODULOS")
                    column_names = [desc[0] for desc in cursor.description]
                    modulosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
                udcConn.close()
            except Exception as e:
                return JsonResponse({'error': str(e)})

            context = {
                "modulos": modulosData
            }
            
            return render(request, 'usuarios/admin_aplicaciones.html', context)

def global_listado_usuario(request):
    user_id = request.session.get('user_id', '')

    if user_id == '':  
        return HttpResponseRedirect(reverse('login'))
    else:
        return render(request, 'usuarios/listado_usuario.html')

def global_listado_grupo(request):
    user_id = request.session.get('user_id', '')
    adminIT = request.session.get('globalAdminIT', 0)

    if user_id == '':  
        return HttpResponseRedirect(reverse('login'))
    if adminIT == 1:

            modulosData = ""
            
            try:
                udcConn = connections['global_nube']
                with udcConn.cursor() as cursor:
                    cursor.callproc("GS_GET_ALL_MODULOS")
                    column_names = [desc[0] for desc in cursor.description]
                    modulosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
                udcConn.close()
            except Exception as e:
                return JsonResponse({'error': str(e)})

            context = {
                "modulos": modulosData
            }
            return render(request, 'grupos/listado_grupo.html', context)

def global_usuarios_grupo(request):
    user_id = request.session.get('user_id', '')
    adminIT = request.session.get('globalAdminIT', 0)

    if user_id == '':  
        return HttpResponseRedirect(reverse('login'))
    if adminIT == 1:

            modulosData = ""
            
            try:
                udcConn = connections['global_nube']
                with udcConn.cursor() as cursor:
                    cursor.callproc("GS_GET_ALL_MODULOS")
                    column_names = [desc[0] for desc in cursor.description]
                    modulosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
                udcConn.close()
            except Exception as e:
                return JsonResponse({'error': str(e)})

            context = {
                "modulos": modulosData
            }
            return render(request, 'usuarios/usuarios_grupo.html', context)
    
def obtener_menus_data(request):
    menusData = []
    if request.method == "POST":
        modulo_id = request.POST.get("modulo_id")
       
        try:
            udcConn = connections['global_nube']
            with udcConn.cursor() as cursor:
               
                cursor.execute("SELECT PKMenu,Boton, Nombre, Pagina, Grupo, Posicion,Verificado as Estado FROM menus WHERE fkModulo = %s ORDER BY Grupo, Posicion;", [modulo_id])
                column_names = [desc[0] for desc in cursor.description]
                
                # Convertir valores de tipo BIT (bytes) a int (0 o 1)
                menusData = [
                    {str(key): (int.from_bytes(value, "little") if isinstance(value, bytes) else value)
                     for key, value in zip(column_names, row)}
                    for row in cursor.fetchall()
                ]
            
            return JsonResponse({'data': menusData})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
    
def obtener_usuarios_data(request):
    
    usuariosData = ''
    try:

        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            cursor.execute("SELECT PKUsuario, Nombre, Apellido, Usuario, Contrasena, Estado, PassRequerido, Descuento, Ventas, Telefono, Comisiones FROM usuarios where Estado = 1 ORDER BY Usuario")
            column_names = [desc[0] for desc in cursor.description]
            usuariosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]

            udcConn.close()
        
        return JsonResponse({'data': usuariosData})
    except Exception as e:
        return JsonResponse({'error': str(e)})


def obtener_grupos_data(request):
    gruposData = ''
    if request.method == "POST":
        modulo_id = request.POST.get("modulo_id")
       
        try:
            udcConn = connections['global_nube']
            with udcConn.cursor() as cursor:
               
                cursor.execute("SELECT PKgrupo, Nombre, Descripcion, fkModulo FROM grupos WHERE (fkModulo = %s) ORDER BY Nombre;", [modulo_id])
                column_names = [desc[0] for desc in cursor.description]
                gruposData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]

                udcConn.close()

            return JsonResponse({'data': gruposData})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

def asignar_usuario_grupo(request):
    if request.method == "POST":
        grupo_id = request.POST.get("grupo_id")
        usuario_id = request.POST.get("usuario_id")

        try:
            udcConn = connections['global_nube']
            with udcConn.cursor() as cursor:
                # Llamar al procedimiento almacenado
                cursor.callproc("mySP_Insert_Usuarios_Grupo", [grupo_id, usuario_id])

            return JsonResponse({"status": "success", "message": "Usuario asignado correctamente."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

  
def quitar_usuario_grupo(request):
    if request.method == "POST":
        grupo_id = request.POST.get("grupo_id")
        usuario_id = request.POST.get("usuario_id")

        try:
            udcConn = connections['global_nube']
            with udcConn.cursor() as cursor:
                # Llamar al procedimiento almacenado
                cursor.callproc("mySP_Delete_Usuarios_Grupo", [grupo_id, usuario_id])

            return JsonResponse({"status": "success", "message": "Usuario quitado correctamente."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
#SIN PROCEDIMIENTO    
def delete_menu(request):
    try:
        menu_id = request.POST.get('menu_id')

        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.execute('DELETE FROM menus WHERE PKMenu = %s', [
                menu_id,
            ]) 
            results = cursor.fetchall()

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)
        
def asignar_usuarios_admin(request):
    if request.method == "POST":
        modulo_id = request.POST.get("modulo_id")
        usuario_id = request.POST.get("usuario_id")

        try:
            udcConn = connections['global_nube']
            with udcConn.cursor() as cursor:
                # Llamar al procedimiento almacenado
                cursor.callproc("mySP_Insert_Usuarios_Admin", [modulo_id, usuario_id])

                # Actualizar el usuario para establecer PassRequerido = 2
                cursor.execute("UPDATE usuarios SET PassRequerido = 2 WHERE PKusuario = %s;", [usuario_id])

                # Eliminar registros existentes en usuarios_modulo para evitar duplicados
                cursor.execute("DELETE FROM usuarios_modulo WHERE fkModulo = %s AND fkUsuario = %s;", [modulo_id, usuario_id])

                # Insertar el nuevo registro en usuarios_modulo
                cursor.execute("INSERT INTO usuarios_modulo (fkModulo, fkUsuario) VALUES (%s, %s);", [modulo_id, usuario_id])

            return JsonResponse({"status": "success", "message": "Usuario admin asignado correctamente."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
        
def quitar_usuarios_admin(request):
    if request.method == "POST":
        modulo_id = request.POST.get("modulo_id")
        usuario_id = request.POST.get("usuario_id")

        try:
            udcConn = connections['global_nube']
            with udcConn.cursor() as cursor:
                
                cursor.callproc("mySP_Delete_Usuarios_Admin", [modulo_id, usuario_id])

                
                cursor.execute("UPDATE usuarios SET  PassRequerido = 1 WHERE PKusuario = %s;", [usuario_id])

            return JsonResponse({"status": "success", "message": "Usuario admin se quitó correctamente."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
        

            
""" Call mySP_Insert_acciones_Usuario({0}, {1}, {2})", Padre, Hijo, Permiso"""   

def asignar_accion(request):
    """ Asigna un módulo a un usuario usando un procedimiento almacenado """
    if request.method == "POST":
        usuario_id = request.POST.get("usuario_id")
        accion_id = request.POST.get("accion_id")

        try:
            udcConn = connections['global_nube']
            with udcConn.cursor() as cursor:
                """ cursor.callproc("INSERT INTO acciones_usuario (fkUsuario,fkAccion,Permiso)VALUES (p01_fkUsuario, p02_fkAccion, p03_Permiso);", [modulo_id,usuario_id])"""
                cursor.execute("INSERT INTO acciones_usuario (fkUsuario,fkAccion,Permiso)VALUES (%s, %s,%s);", [usuario_id,accion_id,1])
            return JsonResponse({"status": "success", "message": "Acción asignada correctamente."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

def quitar_accion(request):
    """ Asigna un módulo a un usuario usando un procedimiento almacenado """
    if request.method == "POST":
        usuario_id = request.POST.get("usuario_id")
        accion_id = request.POST.get("accion_id")

        try:
            udcConn = connections['global_nube']
            with udcConn.cursor() as cursor:
                """ cursor.callproc("INSERT INTO Acciones_Usuario (fkUsuario,fkAccion,Permiso)VALUES (p01_fkUsuario, p02_fkAccion, p03_Permiso);", [modulo_id,usuario_id])"""
                cursor.callproc("mySP_Delete_Acciones_Usuario", [usuario_id,accion_id])
            return JsonResponse({"status": "success", "message": "Acción quitada correctamente."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
        
def asignar_modulo(request):
    """ Asigna un módulo a un usuario usando un procedimiento almacenado """
    if request.method == "POST":
        usuario_id = request.POST.get("usuario_id")
        accion_id = request.POST.get("accion_id")

        try:
            udcConn = connections['global_nube']
            with udcConn.cursor() as cursor:
                cursor.callproc("mySP_Delete_acciones_Usuario", [usuario_id,accion_id])
    
            return JsonResponse({"status": "success", "message": "Módulo asignado correctamente."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

def quitar_modulo(request):
    """ Quita un módulo de un usuario usando un procedimiento almacenado """
    if request.method == "POST":
        usuario_id = request.POST.get("usuario_id")
        modulo_id = request.POST.get("modulo_id")

        try:
            udcConn = connections['global_nube']
            with udcConn.cursor() as cursor:
                cursor.callproc("mySP_Delete_Usuarios_Modulo", [modulo_id,usuario_id])

            return JsonResponse({"status": "success", "message": "Módulo quitado correctamente."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})


def global_grupos_usuario(request):
    user_id = request.session.get('user_id', '')
    adminIT = request.session.get('globalAdminIT', 0)

    if user_id == '':
        return HttpResponseRedirect(reverse('login'))
        
    else:
        if adminIT == 1:

            modulosData = ""
            usuariosData = ""
            try:
                udcConn = connections['global_nube']
                with udcConn.cursor() as cursor:
                    cursor.callproc("GS_GET_ALL_MODULOS")
                    column_names = [desc[0] for desc in cursor.description]
                    modulosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
                udcConn.close()
            except Exception as e:
                return JsonResponse({'error': str(e)})

            context = {
                "modulos": modulosData
            }
            
            return render(request, 'usuarios/grupos_del_usuario.html', context)
        
def global_listado_menu(request):
    user_id = request.session.get('user_id', '')
    adminIT = request.session.get('globalAdminIT', 0)

    if user_id == '':
        return HttpResponseRedirect(reverse('login'))
        
    else:
        if adminIT == 1:

            modulosData = ""
            usuariosData = ""
            try:
                udcConn = connections['global_nube']
                with udcConn.cursor() as cursor:
                    cursor.callproc("GS_GET_ALL_MODULOS")
                    column_names = [desc[0] for desc in cursor.description]
                    modulosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
                udcConn.close()
            except Exception as e:
                return JsonResponse({'error': str(e)})

            context = {
                "modulos": modulosData
            }
            
            return render(request, 'menus/listado_menu.html', context)



    
def data_usuario_grupo_asignado(request):
    grupo_id = request.POST.get('grupo_id')

    usuarioGrupoData = ''
    try:

        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            cursor.callproc("mySP_Select_Usuarios_Grupo", [grupo_id])
            column_names = [desc[0] for desc in cursor.description]
            usuarioGrupoData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
            udcConn.close()
        
        return JsonResponse({'data': usuarioGrupoData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    
    
def data_usuario_grupo_disponible(request):
    grupo_id = request.POST.get('grupo_id')

    usuarioGrupoData = ''
    try:

        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            cursor.callproc("mySP_Select_Usuarios_NoExisten_Grupo", [grupo_id])
            column_names = [desc[0] for desc in cursor.description]
            usuarioGrupoData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
            udcConn.close()
        
        return JsonResponse({'data': usuarioGrupoData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def data_usuario_admin_disponibles(request):
    
    
    modulo = request.POST.get('varModulo')

    adminUsuariosData = ''
    try:

        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            cursor.callproc("mySP_Select_Usuarios_NoExisten_Admin", [modulo])
            column_names = [desc[0] for desc in cursor.description]
            adminUsuariosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
            udcConn.close()
        
        return JsonResponse({'data': adminUsuariosData})
    except Exception as e:
        return JsonResponse({'error': str(e)})

def data_usuario_admin_asignados(request):
    
    
    modulo = request.POST.get('varModulo')

    adminUsuariosData = ''
    try:

        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            cursor.callproc("mySP_Select_Usuarios_Admin", [modulo])
            column_names = [desc[0] for desc in cursor.description]
            adminUsuariosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
            udcConn.close()
        
        return JsonResponse({'data': adminUsuariosData})
    except Exception as e:
        return JsonResponse({'error': str(e)})       

def data_acciones_disponibles(request):
    
    usuario = request.POST.get('varUsuario')
    modulo = request.POST.get('varModulo')

    accionesUsuariosData = ''
    try:

        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            cursor.callproc("mySP_Select_Acciones_NoExisten_Usuario", [usuario,modulo])
            column_names = [desc[0] for desc in cursor.description]
            accionesUsuariosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
            udcConn.close()
        
        return JsonResponse({'data': accionesUsuariosData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    
def data_modulos_disponibles(request):
    
    usuario = request.POST.get('varUsuario')

    modulosUsuariosData = ''
    try:

        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            cursor.callproc("mySP_Select_Modulos_NoExisten_Usuario", [usuario])
            column_names = [desc[0] for desc in cursor.description]
            modulosUsuariosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
            udcConn.close()
        
        return JsonResponse({'data': modulosUsuariosData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    
def data_grupos_disponibles(request):
    
    usuario = request.POST.get('varUsuario')
    modulo = request.POST.get('varModulo')

    gruposUsuariosData = ''
    try:

        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            cursor.callproc("mySP_Select_Grupos_NoExisten_Usuario_gs", [usuario, modulo])
            column_names = [desc[0] for desc in cursor.description]
            gruposUsuariosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]

            udcConn.close()
        
        return JsonResponse({'data': gruposUsuariosData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    
def data_acciones_asignadas(request):
    usuario = request.POST.get('varUsuario')
    modulo = request.POST.get('varModulo')

    accionesUsuariosData = []
    try:
        
        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            
            cursor.callproc("mySP_Select_Acciones_Usuario", [usuario, modulo])
            column_names = [desc[0] for desc in cursor.description]

           
            accionesUsuariosData = []
            for row in cursor.fetchall():
                row_dict = dict(zip(map(str, column_names), row))
                for key, value in row_dict.items():
                    if isinstance(value, bytes):
                        row_dict[key] = value.decode('utf-8', errors='ignore')  # Decode bytes to string
                        accionesUsuariosData.append(row_dict)

            # Close connection
            udcConn.close()
        
        return JsonResponse({'data': accionesUsuariosData})
    
    except Exception as e:
        return JsonResponse({'error': str(e)})

def data_modulos_asignados(request):
    
    usuario = request.POST.get('varUsuario')
    

    modulosUsuariosData = ''
    try:

        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            cursor.callproc("mySP_Select_Modulos_Usuario", [usuario])
            column_names = [desc[0] for desc in cursor.description]
            modulosUsuariosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]

            udcConn.close()
        
        return JsonResponse({'data': modulosUsuariosData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    
def data_grupos_asignados(request):
    
    usuario = request.POST.get('varUsuario')
    modulo = request.POST.get('varModulo')

    gruposUsuariosData = ''
    try:

        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            cursor.callproc("mySP_Select_Grupos_Usuario_gs", [usuario, modulo])
            column_names = [desc[0] for desc in cursor.description]
            gruposUsuariosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]

            udcConn.close()
        
        return JsonResponse({'data': gruposUsuariosData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    
    
def data_usuarios(request):
    
    usuariosData = ''
    try:
        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            cursor.execute("SELECT PKUsuario, Nombre, Apellido, Usuario,Estado FROM usuarios where Estado = 1 ORDER BY Usuario")
            column_names = [desc[0] for desc in cursor.description]
            usuariosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        return JsonResponse({'data': usuariosData})
    except Exception as e:
        return JsonResponse({'error': str(e)})

def data_usuarios_especial(request):
    
    try:
        estado = request.POST.get('estado') 

        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            if estado == '0':  
                cursor.execute('SELECT PKUsuario, Nombre, Usuario, Estado, Contrasena FROM usuarios')
            else:
                cursor.execute('SELECT PKUsuario, Nombre, Usuario, Estado, Contrasena FROM usuarios WHERE Estado = %s', [estado])

            column_names = [desc[0] for desc in cursor.description]
            usuariosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        return JsonResponse({'data': usuariosData})

    except Exception as e:
        return JsonResponse({'data': [], 'error': str(e)})

def update_grupo(request):
    try:
        grupo_id = request.POST.get('grupo_id')
        modulo_id = request.POST.get('modulo_id')
        nombre = request.POST.get('nombre')
        Descripcion = request.POST.get('descripcion')
    
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.execute('UPDATE grupos SET  Nombre = %s,Descripcion = %s, fkModulo = %s WHERE PKgrupo = %s ', [
                nombre,
                Descripcion,
                modulo_id,
                grupo_id,
            ]) 
            results = cursor.fetchall()

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)

def update_menu(request):
    try:
        nombre= request.POST.get('nombre')
        boton = request.POST.get('boton')
        pagina = request.POST.get('pagina')
        grupo = request.POST.get('grupo')
        posicion = request.POST.get('posicion')
        modulo_id = request.POST.get('modulo_id')
        menu_id = request.POST.get('menu_id')

        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.execute('UPDATE menus SET  Nombre = %s,fkModulo = %s, Boton = %s, Pagina = %s, Grupo = %s, Posicion = %s WHERE PKMenu = %s', [
                nombre,
                modulo_id,
                boton,
                pagina,
                grupo,
                posicion,
                menu_id,
            ]) 
            results = cursor.fetchall()

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)

# No existe SP en BD
def insert_grupo(request):
    try:
        modulo_id = request.POST.get('modulo_id')
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
    
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.execute('INSERT grupos SET  Nombre = %s,Descripcion = %s, fkModulo = %s', [
                nombre,
                descripcion,
                modulo_id,
            ]) 
            results = cursor.fetchall()

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)

def insert_menu(request):
    try:
        nombre= request.POST.get('nombre')
        boton = request.POST.get('boton')
        pagina = request.POST.get('pagina')
        grupo = request.POST.get('grupo')
        posicion = request.POST.get('posicion')
        modulo_id = request.POST.get('modulo_id')
        
    
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.execute('INSERT menus SET  Nombre = %s,fkModulo = %s, Boton = %s, Pagina = %s, Grupo = %s, Posicion = %s', [
                nombre,
                modulo_id,
                boton,
                pagina,
                grupo,
                posicion,
            ]) 
            results = cursor.fetchall()

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)

# No existe SP en BD
def delete_grupo(request):
    try:
        grupo_id = request.POST.get('grupo_id')

        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.execute('DELETE FROM grupos WHERE PKgrupo = %s', [
                grupo_id,
            ]) 
            results = cursor.fetchall()

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)



def update_password_usuario(request):
    try:
        id_usuario = request.POST.get('id_usuario')
        password = request.POST.get('password')

        varUsuario = request.session.get('user', '')

        # bytes_pass = password.encode('utf-8')
        # base64_pass = base64.b64encode(bytes_pass)
        # password64 = base64_pass.decode('utf-8')

        php_script_path = './DAC/views/md5.php'
        result = subprocess.run(['php', php_script_path, password], stdout=subprocess.PIPE)
        password_md5 = result.stdout.decode('utf-8').strip()

    
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.execute("UPDATE usuarios SET  Contrasena = %s WHERE PKUsuario = %s", [
                password_md5,
                id_usuario,
            ]) 
            results = cursor.fetchall()

        with appConn.cursor() as cursor:
            sql = """INSERT INTO bitacora
                        (fkUsuario ,Contrasena, creado_por)
                        VALUES (%s ,%s, %s );"""
            cursor.execute(sql, [id_usuario,  password_md5, varUsuario]) 
            results = cursor.fetchall()

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)

def update_nombrecompleto_usuario(request):
    try:
        usuario = request.POST.get('usuario')
        nombre = request.POST.get('nombre')
    
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.execute('UPDATE usuarios SET  Nombre = %s WHERE Usuario = %s ', [
                nombre,
                usuario,
            ]) 
            results = cursor.fetchall()

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)

def update_usuario_usuario(request):
    try:
        usuarioActual = request.POST.get('usuarioActual')
        usuarioNuevo = request.POST.get('usuarioNuevo')
    
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.execute('UPDATE usuarios SET  Usuario = %s WHERE Usuario = %s ', [
                usuarioNuevo,
                usuarioActual,
            ]) 
            results = cursor.fetchall()

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)

def update_estado_usuario(request):
    try:
        usuario = request.POST.get('usuario')
        estado = request.POST.get('estado')  # '1' para habilitar, '2' para retirar

        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.execute('UPDATE usuarios SET Estado = %s WHERE Usuario = %s', [
                estado,
                usuario,
            ]) 
            appConn.commit()  # Confirmar la actualización

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)

# Sin SP
def update_estado_menu(request):
    try:
        menu_id = request.POST.get('menu_id')
        estado = request.POST.get('estado')  # '1' para habilitar, '0' para retirar

        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            if estado == '1':
                sql = 'UPDATE menus SET Verificado = 1 WHERE PKMenu = %s'
            else:
                sql = 'UPDATE menus SET Verificado = 0 WHERE PKMenu = %s'
            cursor.execute(sql, [
                menu_id,
            ]) 
            appConn.commit()  # Confirmar la actualización

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)


def descargar_archivo_onedrive():
    archivo_local = "Diccionario.xlsx"

    url_onedrive = "https://cabajal-my.sharepoint.com/personal/soportetecnico_carbajalhn_com/_layouts/15/download.aspx?share=EVt8VgO__3NEq40gYFu-3P4BSykvJPRKPoOelx_XsmmKEw"

    if os.path.exists(archivo_local):
        return archivo_local

    try:
        response = requests.get(url_onedrive, allow_redirects=True)

        if response.status_code == 200:
            with open(archivo_local, "wb") as file:
                file.write(response.content)
            return archivo_local
        else:
            return None

    except requests.exceptions.RequestException as e:
        return None

def obtener_contrasena(request):

    hash_recibido = request.POST.get("hash")

    try:
        bytes_decodificados = base64.b64decode(hash_recibido)

        contrasenia = bytes_decodificados.decode('utf-8')

        return JsonResponse({"contraseña": contrasenia}, status=200)


    except Exception as e:
        return JsonResponse({"contraseñas": "Error al procesar el archivo", "error": str(e)}, status=500)







    
def obtener_historial_contraseña(request):
    php_script_path = './DAC/views/md5.php'
    # php_script_path = '/var/www/html/TESTING/DAC_D/DAC/views/md5.php'

    varUsuario = request.POST.get('varUsuario')

    contrasenasData = []
    try:
        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            sql = """SELECT contrasena FROM bitacora WHERE fkUsuario = %s"""
            cursor.execute(sql, [varUsuario])
            column_names = [desc[0] for desc in cursor.description]
            contrasenasData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        bitacora_archivo_local = "bitacora.txt"
        # bitacora_archivo_local = '/var/www/html/TESTING/DAC_D/GLOBAL/views/bitacora.txt'

        if bitacora_archivo_local is None:
            return JsonResponse({"error": "No se pudo descargar el archivo"}, status=500)

        contrasenas_encontradas = []  

        try:
            with open(bitacora_archivo_local, "r", encoding="utf-8") as file:
                for linea in file:
                    password = linea.strip()
                    
                    result = subprocess.run(['php', php_script_path, password], stdout=subprocess.PIPE)
                    crypted_pass = result.stdout.decode('utf-8').strip()

                    for contrasena_db in contrasenasData:
                        contrasena_en_base = contrasena_db.get('contrasena', None)

                        if contrasena_en_base is None:
                            continue 


                        if crypted_pass == contrasena_en_base:
                            contrasenas_encontradas.append(password) 

            
            return JsonResponse({"contrasenas_anteriores": contrasenas_encontradas}, status=200)

        except Exception as e:
            return JsonResponse({"contrasenas": "Error al procesar el archivo", "error": str(e)}, status=500)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def insert_usuario_listado(request):
    
    varNombre = request.POST.get('varNombre')
    varUsuario = request.POST.get('varUsuario')
    varPassword = request.POST.get('varPassword')
    varEmpleado = request.POST.get('varEmpleado')
    
    idUsuario = None

    php_script_path = './DAC/views/md5.php'
    result = subprocess.run(['php', php_script_path, varPassword], stdout=subprocess.PIPE)
    password_md5 = result.stdout.decode('utf-8').strip()

    try:
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.callproc('GS_INSERTAR_USUARIO', [varNombre, varUsuario, password_md5])
            results = cursor.fetchall()

            if results:
                idUsuario = results[0][0]
                print("usuario creado? "+ str(idUsuario))
                if idUsuario != 0:
                    appConn = connections['udc_dev1']
                    with appConn.cursor() as cursor:
                        cursor.callproc('TH_UPDATE_TH_EMPLEADO_FICHA_USUARIO', [varEmpleado, idUsuario])
                        cursor.fetchall()
                else:
                    datos = {'save': 0, 'error': 'Ya hay un empleado con ese usuario'}
                    return JsonResponse(datos)
            

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}

    return JsonResponse(datos)


def insert_usuario_grupo(request):
    
    varUsuario = request.POST.get('varUsuario')
    varGrupo = request.POST.get('varGrupo')
    
    try:
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.callproc('mySP_Insert_Usuarios_grupo', [
                varGrupo,
                varUsuario
            ])       
            results = cursor.fetchall()  

        
        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)

def eliminar_usuario_grupo(request):

    varGrupo = request.POST.get('varGrupo')
    varUsuario = request.POST.get('varUsuario')
    
    try:
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.callproc('mySP_Delete_Usuarios_grupo', [
                varGrupo,
                varUsuario
            ])       
            results = cursor.fetchall()  

        
        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)


def global_menus_usuario(request):
    user_id = request.session.get('user_id', '')
    adminIT = request.session.get('globalAdminIT', 0)

    if user_id == '':
        # return HttpResponseRedirect(reverse('login'))
         a =2
    else:
        if adminIT == 1:

            modulosMenusUsuarioData = ""
            usuariosMenusUsuarioData = ""

            try:
                udcConn = connections['global_nube']
                with udcConn.cursor() as cursor:
                    cursor.callproc("GS_GET_ALL_MODULOS")
                    column_names = [desc[0] for desc in cursor.description]
                    modulosMenusUsuarioData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
                udcConn.close()
            except Exception as e:
                return JsonResponse({'error': str(e)})

            context = {
                "modulos": modulosMenusUsuarioData
            }
            
            return render(request, 'usuarios/menus_del_usuario.html', context)    

def get_usuarios_menus_usuarios(request):
    varModulo = request.POST.get('varModulo')

    usuariosMenusData = ''
    try:
        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            cursor.callproc("mySP_Select_Usuarios_Modulo",[varModulo])
            column_names = [desc[0] for desc in cursor.description]
            usuariosMenusData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        return JsonResponse({'data': usuariosMenusData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def data_grupos_usuarios_menus_usuarios(request):
    varModulo = request.POST.get('varModulo')
    varUsuario = request.POST.get('varUsuario')

    gruposUsuariosMenusData = ''
    try:
        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            cursor.callproc("mySP_Select_Grupos_Usuario_gs",[varUsuario, varModulo])
            column_names = [desc[0] for desc in cursor.description]
            gruposUsuariosMenusData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        return JsonResponse({'data': gruposUsuariosMenusData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def data_menus_disponibles(request):
    varModulo = request.POST.get('varModulo')

    if not varModulo:  # Verifica si el módulo fue enviado
        return JsonResponse({'error': 'El parámetro varModulo es requerido'}, status=400)

    try:
        with connections['global_nube'].cursor() as cursor:
            consulta = """
                SELECT menus.PKMenu, menus.fkModulo, menus.Posicion, menus.Nombre, 
                       menus.NoOrden, menus.TipoMenu, menus.Pagina, menus.Grupo, 
                       menus.Boton, menus.Verificado, false as Autorizado, -1 as Permiso, view_paginas_menus.Nombre AS NombrePagina 
                FROM menus 
                INNER JOIN view_paginas_menus ON menus.Pagina = view_paginas_menus.Pagina 
                WHERE menus.fkModulo = %s 
                ORDER BY menus.Boton
            """
            cursor.execute(consulta, [varModulo])
            column_names = [desc[0] for desc in cursor.description]
            menusDisponiblesData = []
            for row in cursor.fetchall():
                menu_data = dict(zip(column_names, row))
                
                menu_data['Verificado'] = bool(menu_data['Verificado'])
                
                menu_data['Autorizado'] = bool(menu_data['Autorizado'])
                
                menusDisponiblesData.append(menu_data)

        return JsonResponse({'data': menusDisponiblesData})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


    
#hay que hacer una correccion en la base de datos debido a que el nombre de la tabla esta mal escrito
def data_menus_asignados(request):
    varUsuario = request.POST.get('varUsuario')
    varModulo = request.POST.get('varModulo')

    menusAsignadosData = ''
    try:
        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            cursor.callproc("mySP_Select_Menus_Usuario",[varUsuario, varModulo])
            column_names = [desc[0] for desc in cursor.description]
            menusAsignadosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        return JsonResponse({'data': menusAsignadosData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    
    
def data_menus_grupo(request):
    varGrupo = request.POST.get('varGrupo')
    varModulo = request.POST.get('varModulo')

    menusGrupoData = ''
    try:
        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            cursor.callproc("mySP_Select_Menus_Grupo",[varGrupo, varModulo])
            column_names = [desc[0] for desc in cursor.description]
            menusGrupoData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        return JsonResponse({'data': menusGrupoData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def data_menus_usuario(request):
    varUsuario = request.POST.get('varUsuario')
    varModulo = request.POST.get('varModulo')

    menusUsuariosData = ''
    try:
        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            cursor.callproc("mySP_Select_Menus_Usuario",[varUsuario, varModulo])
            column_names = [desc[0] for desc in cursor.description]
            menusUsuariosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        return JsonResponse({'data': menusUsuariosData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    
def delete_insert_menu_usuario(request):
    varIdRegistro = request.POST.get('varIdRegistro')
    varPKMenu = request.POST.get('varPKMenu')
    varSiguiente = request.POST.get('varSiguiente')
    sql_query = ""

    try:
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            if int(varSiguiente) == -1:
                sql_query = """
                    DELETE FROM menus_usuario
                    WHERE fkUsuario = %s AND fkMenu = %s
                """
                cursor.execute(sql_query, [varIdRegistro, varPKMenu])
            else:
                sql_query = """
                    DELETE FROM menus_usuario
                    WHERE fkUsuario = %s AND fkMenu = %s
                """
                cursor.execute(sql_query, [varIdRegistro, varPKMenu])

                sql_query = """
                    INSERT INTO menus_usuario (fkUsuario, fkMenu, Permiso)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(sql_query, [varIdRegistro, varPKMenu, varSiguiente])
            
            appConn.commit()

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)


def delete_menus_usuario(request):
    varIdRegistro = request.POST.get('varIdRegistro')

    try:
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            sql_query = """
                DELETE FROM menus_usuario
                WHERE fkUsuario = %s
            """
            cursor.execute(sql_query, [varIdRegistro])
            
            appConn.commit()

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)

def global_admin_it(request):
    user_id = request.session.get('user_id', '')
    adminIT = request.session.get('globalAdminIT', 0)

    if user_id == '':  
        return HttpResponseRedirect(reverse('login'))
    if adminIT == 1:
            
            return render(request, 'usuarios/admin_it.html')
    

def get_modulos_admin_it(request):
    modulosMenusUsuarioData = ""

    try:
        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            cursor.callproc("GS_GET_ALL_MODULOS")
            column_names = [desc[0] for desc in cursor.description]
            modulosMenusUsuarioData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        return JsonResponse({'data': modulosMenusUsuarioData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def get_usuarios_disponibles_admin_it_data(request):
    
    varModulo = request.POST.get('varModulo')
    usuariosITDisponiblesData = ""

    try:
        udcConn = connections['global_nube']

        with udcConn.cursor() as cursor:
            cursor.callproc("mySP_Select_Usuarios_NoExisten_Admin_IT", [varModulo])
            column_names = [desc[0] for desc in cursor.description]
            usuariosITDisponiblesData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        return JsonResponse({'data': usuariosITDisponiblesData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def get_usuarios_asignados_admin_it_data(request):

    varModulo = request.POST.get('varModulo')
    usuariosItAsignadosData = ""

    try:
        udcConn = connections['global_nube']

        with udcConn.cursor() as cursor:
            cursor.callproc("mySP_Select_Usuarios_Admin_IT", [varModulo])
            column_names = [desc[0] for desc in cursor.description]
            usuariosItAsignadosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        return JsonResponse({'data': usuariosItAsignadosData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def insert_usuario_it(request):
    
    varUsuario = request.POST.get('varUsuario')
    varModulo = request.POST.get('varModulo')
    
    try:
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.callproc('mySP_Insert_Usuarios_Admin_IT', [varModulo, varUsuario])       
            results = cursor.fetchall()  

        
        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)

def eliminar_usuario_it(request):

    varUsuario = request.POST.get('varUsuario')
    varModulo = request.POST.get('varModulo')
    
    try:
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.callproc('mySP_Delete_Usuarios_Admin_it', [varModulo, varUsuario])       
            results = cursor.fetchall()  

        
        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)


def global_menus_grupo(request):
    user_id = request.session.get('user_id', '')
    adminIT = request.session.get('globalAdminIT', 0)

    if user_id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        if adminIT == 1:

            modulosMenusGrupoData = ""

            try:
                udcConn = connections['global_nube']
                with udcConn.cursor() as cursor:
                    cursor.callproc("GS_GET_ALL_MODULOS")
                    column_names = [desc[0] for desc in cursor.description]
                    modulosMenusGrupoData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
                udcConn.close()
            except Exception as e:
                return JsonResponse({'error': str(e)})

            context = {
                "modulos": modulosMenusGrupoData
            }
            
            return render(request, 'grupos/menus_del_grupo.html', context)   
        


def get_menus_grupo_grupos_data(request):

    varModulo = request.POST.get('varModulo')

    try:
        udcConn = connections['global_nube']

        with udcConn.cursor() as cursor:
            sql = """SELECT PKgrupo, Nombre, Descripcion, IsBuiltIn, fkModulo
                      FROM grupos
                      WHERE (fkModulo = %s)
                      ORDER BY Nombre"""
            cursor.execute(sql, [varModulo])
            column_names = [desc[0] for desc in cursor.description]
            gruposData = []
            for row in cursor.fetchall():
                grupos_data = dict(zip(column_names, row))
                
                grupos_data['IsBuiltIn'] = bool(grupos_data['IsBuiltIn'])
                
                gruposData.append(grupos_data)
            
        
        udcConn.close()

        return JsonResponse({'data': gruposData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def get_menus_grupo_menus_data(request):

    varModulo = request.POST.get('varModulo')
    

    try:
        udcConn = connections['global_nube']

        with udcConn.cursor() as cursor:
            sql = """
                SELECT 
                    menus.PKMenu, 
                    menus.fkModulo, 
                    menus.Posicion, 
                    menus.Nombre, 
                    menus.NoOrden, 
                    menus.TipoMenu, 
                    menus.Pagina, 
                    menus.Grupo, 
                    menus.Boton, 
                    false as Autorizado, 
                    menus.Verificado, 
                    view_paginas_menus.Nombre AS NombrePagina
                FROM 
                    menus
                INNER JOIN 
                    view_paginas_menus 
                ON 
                    menus.Pagina = view_paginas_menus.Pagina
                WHERE 
                    menus.fkModulo = %s
                ORDER BY 
                    menus.Boton
            """
            cursor.execute(sql, [varModulo])
            column_names = [desc[0] for desc in cursor.description]

            menusData = []
            for row in cursor.fetchall():
                menu_data = dict(zip(column_names, row))
                
                menu_data['Verificado'] = bool(menu_data['Verificado'])
                menu_data['Autorizado'] = bool(menu_data['Autorizado'])
                
                menusData.append(menu_data)
        
        udcConn.close()

        return JsonResponse({'data': menusData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def insert_delete_menu_grupo(request):
    varIdGrupo = request.POST.get('varIdGrupo')
    varPKMenu = request.POST.get('varPKMenu')
    varAutorizado = request.POST.get('varAutorizado')
    sql_query = ""

    try:
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:

            if varAutorizado:
                sql_query = """
                    DELETE FROM menus_grupo WHERE fkGrupo = %s AND fkMenu = %s
                """
            else:
                sql_query = """
                    INSERT INTO menus_grupo (fkGrupo, fkMenu) VALUES (%s, %s)
                """
            cursor.execute(sql_query, [varIdGrupo, varPKMenu])
            
            appConn.commit()

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)



def global_acciones_grupo(request):
    user_id = request.session.get('user_id', '')
    adminIT = request.session.get('globalAdminIT', 0)

    if user_id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        if adminIT == 1:

            modulosAccionesGrupoData = ""

            try:
                udcConn = connections['global_nube']
                with udcConn.cursor() as cursor:
                    cursor.callproc("GS_GET_ALL_MODULOS")
                    column_names = [desc[0] for desc in cursor.description]
                    modulosAccionesGrupoData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
                udcConn.close()
            except Exception as e:
                return JsonResponse({'error': str(e)})

            context = {
                "modulos": modulosAccionesGrupoData
            }
            
            return render(request, 'grupos/acciones_del_grupo.html', context)   
        

def get_acciones_grupos_data(request):

    varModulo = request.POST.get('varModulo')

    try:
        udcConn = connections['global_nube']

        with udcConn.cursor() as cursor:

            sql = """SELECT        
                    PKgrupo, Nombre, Descripcion, IsBuiltIn, fkModulo
                    FROM grupos
                    WHERE (fkModulo = %s)
                    ORDER BY Nombre"""
            
            cursor.execute(sql, [varModulo])
            column_names = [desc[0] for desc in cursor.description]
            accionesGruposData = []
            for row in cursor.fetchall():
                grupos_data = dict(zip(column_names, row))
                
                grupos_data['IsBuiltIn'] = bool(grupos_data['IsBuiltIn'])
                
                accionesGruposData.append(grupos_data)
            
        udcConn.close()

        return JsonResponse({'data': accionesGruposData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def get_acciones_grupos_diponibles_data(request):

    varGrupo = request.POST.get('varGrupo')
    varModulo = request.POST.get('varModulo')

    accionesGruposDisponiblesData = ""

    try:
        udcConn = connections['global_nube']

        with udcConn.cursor() as cursor:
            
            #el procedimiento almacenado necesita modificarse, no encuentra la tabla Acciones
            cursor.callproc("mySP_Select_Acciones_NoExisten_Grupo", [varGrupo, varModulo])
            column_names = [desc[0] for desc in cursor.description]
            accionesGruposDisponiblesData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]        

        udcConn.close()

        return JsonResponse({'data': accionesGruposDisponiblesData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def get_acciones_grupos_asignadas_data(request):

    varGrupo = request.POST.get('varGrupo')
    varModulo = request.POST.get('varModulo')

    accionesGruposAsignadasData = ""

    try:
        udcConn = connections['global_nube']

        with udcConn.cursor() as cursor:
            
            cursor.callproc("mySP_Select_Acciones_Grupo", [varGrupo, varModulo])
            column_names = [desc[0] for desc in cursor.description]
            accionesGruposAsignadasData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        return JsonResponse({'data': accionesGruposAsignadasData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    


#el procedimiento almacenado utilizado necesito modificarse levemente, acciones_grupo estaba mal escrito (Acciones_grupo)
def insert_accion_grupo(request):
    
    varAccion = request.POST.get('varAccion')
    varGrupo = request.POST.get('varGrupo')
    
    try:
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.callproc('mySP_Insert_Acciones_Grupo', [varGrupo, varAccion])       
            results = cursor.fetchall()  

        
        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)

def eliminar_accion_grupo(request):

    varAccion = request.POST.get('varAccion')
    varGrupo = request.POST.get('varGrupo')
    
    try:
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.callproc('mySP_Delete_Acciones_Grupo', [varGrupo, varAccion])       
            results = cursor.fetchall()  

        
        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)


def global_usuarios_autorizados_modulos(request):
    user_id = request.session.get('user_id', '')
    adminIT = request.session.get('globalAdminIT', 0)

    if user_id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        if adminIT == 1:            
            return render(request, 'modulos/usuarios_autorizados_modulos.html')  
        

def get_usuarios_autorizados_modulos(request):

    varGrupo = request.POST.get('varGrupo')
    varModulo = request.POST.get('varModulo')

    usuaiosAutorizadosModulosData = ""

    try:
        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            cursor.callproc("GS_GET_ALL_MODULOS")
            column_names = [desc[0] for desc in cursor.description]
            usuaiosAutorizadosModulosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        return JsonResponse({'data': usuaiosAutorizadosModulosData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def get_usuarios_autorizados_modulos_usuarios_disponibles_data(request):

    varModulo = request.POST.get('varModulo')

    usuariosDisponiblesData = ""

    try:
        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            cursor.callproc("mySP_Select_Usuarios_NoExisten_Modulo", [varModulo])
            column_names = [desc[0] for desc in cursor.description]
            usuariosDisponiblesData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        return JsonResponse({'data': usuariosDisponiblesData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def get_usuarios_autorizados_modulos_usuarios_asignados_data(request):

    varModulo = request.POST.get('varModulo')

    usuariosAsignadosData = ""

    try:
        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            cursor.callproc("mySP_Select_Usuarios_Modulo", [varModulo])
            column_names = [desc[0] for desc in cursor.description]
            usuariosAsignadosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        return JsonResponse({'data': usuariosAsignadosData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def insert_usuarios_autorizados_modulos_usuarios_disponible(request):
    
    varUsuario = request.POST.get('varUsuario')
    varModulo = request.POST.get('varModulo')
    
    try:
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.callproc('mySP_Insert_Usuarios_Modulo', [varModulo, varUsuario])       
            results = cursor.fetchall()  
        
        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)

def eliminar_usuarios_autorizados_modulos_usuarios_asignado(request):

    varUsuario = request.POST.get('varUsuario')
    varModulo = request.POST.get('varModulo')
    
    try:
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.callproc('mySP_Delete_Usuarios_Modulo', [varModulo, varUsuario])       
            results = cursor.fetchall()  

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)



def global_usuarios_de_la_sucursal(request):
    user_id = request.session.get('user_id', '')
    adminIT = request.session.get('globalAdminIT', 0)

    if user_id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        if adminIT == 1:
            
            return render(request, 'sucursales/usuarios_de_la_sucursal.html') 
        

def get_usuarios_de_la_sucursal_sucursales_data(request):

    varGrupo = request.POST.get('varGrupo')
    varModulo = request.POST.get('varModulo')

    sucursalesData = ""

    try:
        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            sql = """SELECT
                        sucursales.PKsucursal,
                        sucursales.CodigoSucursal,
                        sucursales.NombreSucursal,
                        sucursales.NoOrden,
                        sucursales.fkEmpresa,
                        empresas.NombreEmpresa
                        FROM empresas
                        INNER JOIN sucursales
                            ON empresas.PKempresa = sucursales.fkEmpresa
                        ORDER BY sucursales.NoOrden"""
            cursor.execute(sql)
            column_names = [desc[0] for desc in cursor.description]
            sucursalesData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        return JsonResponse({'data': sucursalesData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def get_usuarios_de_la_sucursal_usuarios_disponibles_data(request): 

    varSucursal = request.POST.get('varSucursal')

    usuariosDisponiblesData = ""

    try:
        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            cursor.callproc("mySP_Select_Usuarios_NoExisten_sucursal", [varSucursal])
            column_names = [desc[0] for desc in cursor.description]
            usuariosDisponiblesData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        return JsonResponse({'data': usuariosDisponiblesData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def get_usuarios_de_la_sucursal_usuarios_asignados_data(request):

    varSucursal = request.POST.get('varSucursal')

    usuariosAsignadosData = ""

    try:
        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            cursor.callproc("mySP_Select_Usuarios_Sucursal", [varSucursal])
            column_names = [desc[0] for desc in cursor.description]
            usuariosAsignadosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        return JsonResponse({'data': usuariosAsignadosData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def insert_usuarios_de_la_sucursal_usuarios_disponible(request):
    
    varUsuario = request.POST.get('varUsuario')
    varSucursal = request.POST.get('varSucursal')
    
    try:
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.callproc('mySP_Insert_Usuarios_Sucursal', [varSucursal, varUsuario])       
            results = cursor.fetchall()  
        
        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)

def eliminar_usuarios_de_la_sucursal_usuarios_asignado(request):

    varUsuario = request.POST.get('varUsuario')
    varSucursal = request.POST.get('varSucursal')
    
    try:
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.callproc('mySP_Delete_Usuarios_Sucursal', [varSucursal, varUsuario])       
            results = cursor.fetchall()  

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)


def global_sucursales_del_usuario(request):
    user_id = request.session.get('user_id', '')
    adminIT = request.session.get('globalAdminIT', 0)

    if user_id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        if adminIT == 1:

            usuariosData = ""

            try:
                udcConn = connections['global_nube']
                with udcConn.cursor() as cursor:
                    sql = """SELECT PKUsuario, Nombre, Apellido, Usuario, Contrasena, Estado, PassRequerido, Descuento, Ventas, Telefono, Comisiones
                                FROM usuarios
                                where Estado = 1
                                ORDER BY Usuario"""
                    cursor.execute(sql)
                    column_names = [desc[0] for desc in cursor.description]
                    usuariosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
                udcConn.close()
            except Exception as e:
                return JsonResponse({'error': str(e)})

            context = {
                "usuarios": usuariosData
            }
            
            return render(request, 'sucursales/sucursales_del_usuario.html', context) 


def get_sucursales_del_usuario_usuarios_data(request):

    try:
        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            sql = """SELECT PKUsuario, Nombre, Apellido, Usuario, Contrasena, Estado, PassRequerido, Descuento, Ventas, Telefono, Comisiones
                        FROM usuarios
                        where Estado = 1
                        ORDER BY Usuario"""
            cursor.execute(sql)
            column_names = [desc[0] for desc in cursor.description]

            usuariosData = []
            for row in cursor.fetchall():
                user_data = dict(zip(column_names, row))
                
                user_data['Ventas'] = bool(user_data['Ventas'])
                user_data['Comisiones'] = bool(user_data['Comisiones'])
                
                usuariosData.append(user_data)
        
        udcConn.close()

        return JsonResponse({'data': usuariosData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def get_sucursales_del_usuario_sucursales_data(request):

    sucursalesData = ""

    try:
        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            sql = """SELECT
                        empresas.NombreEmpresa,
                        sucursales.PKsucursal as fkSucursal,
                        sucursales.fkEmpresa,
                        sucursales.NoOrden,
                        sucursales.Estado,
                        sucursales.CodigoSucursal,
                        sucursales.CodigoContable,
                        sucursales.NombreSucursal,
                        '' AS Esta
                        FROM empresas
                        INNER JOIN sucursales
                        ON empresas.PKempresa = sucursales.fkEmpresa"""
            cursor.execute(sql)
            column_names = [desc[0] for desc in cursor.description]
            sucursalesData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        return JsonResponse({'data': sucursalesData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def get_sucursales_del_usuario_data(request):
    varUsuario = request.POST.get('varUsuario')

    sucursalesDelUsuariosData = ""

    try:
        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            cursor.callproc("mySP_Select_Sucursales_Usuario", [varUsuario])
            column_names = [desc[0] for desc in cursor.description]
            sucursalesDelUsuariosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        return JsonResponse({'data': sucursalesDelUsuariosData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def get_sucursales_del_usuario_sucursales_asignadas_data(request):

    sucursalesData = ""

    try:
        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            sql = """SELECT
                        empresas.NombreEmpresa,
                        sucursales.PKsucursal as fkSucursal,
                        sucursales.fkEmpresa,
                        sucursales.NoOrden,
                        sucursales.Estado,
                        sucursales.CodigoSucursal,
                        sucursales.CodigoContable,
                        sucursales.NombreSucursal,
                        '' AS Esta
                        FROM empresas
                        INNER JOIN sucursales
                            ON empresas.PKempresa = sucursales.fkEmpresa"""
            cursor.execute(sql)
            column_names = [desc[0] for desc in cursor.description]
            sucursalesData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        return JsonResponse({'data': sucursalesData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def insert_sucursales_del_usuario_sucursal_disponible(request):
    
    varUsuario = request.POST.get('varUsuario')
    varSucursal = request.POST.get('varSucursal')
    
    try:
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.callproc('mySP_Insert_Usuarios_Sucursal', [varSucursal, varUsuario])       
            results = cursor.fetchall()  
        
        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)

def eliminar_sucursales_del_usuario_sucursal_asignada(request):

    varUsuario = request.POST.get('varUsuario')
    varSucursal = request.POST.get('varSucursal')
    
    try:
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.callproc('mySP_Delete_Usuarios_Sucursal', [varSucursal, varUsuario])       
            results = cursor.fetchall()  

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)


def global_listado_acciones(request):
    user_id = request.session.get('user_id', '')
    adminIT = request.session.get('globalAdminIT', 0)

    if user_id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        if adminIT == 1:

            modulosData = ""

            try:
                udcConn = connections['global_nube']
                with udcConn.cursor() as cursor:
                    cursor.callproc("GS_GET_ALL_MODULOS")
                    column_names = [desc[0] for desc in cursor.description]
                    modulosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
                udcConn.close()
            except Exception as e:
                return JsonResponse({'error': str(e)})

            context = {
                "modulos": modulosData
            }
            
            return render(request, 'acciones/listado_acciones.html', context) 
        

def get_listado_acciones_data(request):

    varModulo = request.POST.get('varModulo')
    accionesData = ""

    try:
        udcConn = connections['global_nube']
        with udcConn.cursor() as cursor:
            sql = """SELECT PKaccion, fkModulo, Nombre, Descripcion
                        FROM acciones
                        WHERE (fkModulo = %s)
                        ORDER BY PKaccion"""
            cursor.execute(sql, [varModulo])
            column_names = [desc[0] for desc in cursor.description]
            accionesData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        return JsonResponse({'data': accionesData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def delete_accion(request):

    varAccion = request.POST.get('varAccion')
    
    try:
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            cursor.execute('DELETE from acciones where PKaccion = %s', [varAccion])       
            results = cursor.fetchall()  

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)



def update_accion(request):

    varAccion = request.POST.get('varAccion')
    varModulo = request.POST.get('varModulo')
    varNombre = request.POST.get('varNombre')
    varDescripcion = request.POST.get('varDescripcion')
    
    try:
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            sql ="""UPDATE acciones 
                    SET
                    fkModulo = %s 
                    ,Nombre = %s 
                    ,Descripcion = %s 
                    WHERE
                    PKaccion = %s 
                    ;"""
            cursor.execute(sql, [varModulo, varNombre, varDescripcion, varAccion])       
            results = cursor.fetchall()  

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)



def create_accion(request):

    varModulo = request.POST.get('varModulo')
    varNombre = request.POST.get('varNombre')
    varDescripcion = request.POST.get('varDescripcion')
    
    try:
        appConn = connections['global_nube']
        with appConn.cursor() as cursor:
            sql = """   INSERT INTO acciones
                        (fkModulo, Nombre, Descripcion)
                        VALUES (%s ,%s ,%s);"""
            
            cursor.execute(sql, [varModulo, varNombre, varDescripcion])       
            results = cursor.fetchall()  

        appConn.close()

        datos = {'save': 1}
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)


def global_config_tipos_solicitud_tokens(request):

    user_id = request.session.get('user_id', '')
    adminIT = request.session.get('globalAdminIT', 0)

    if user_id == '':
        return HttpResponseRedirect(reverse('login'))
    else:
        if adminIT == 1:

            usuariosData = ""
            sucursalesData = ""

            try:
                udcConn = connections['global_nube']
                with udcConn.cursor() as cursor:
                    
                    cursor.callproc("GS_GET_ALL_USUARIOS")
                    column_names = [desc[0] for desc in cursor.description]
                    usuariosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
                udcConn.close()
            except Exception as e:
                return JsonResponse({'error': str(e)})
            

            try:
                udcConn = connections['global_nube']
                with udcConn.cursor() as cursor:
                    
                    cursor.callproc("GS_GET_SUCURSALES")
                    column_names = [desc[0] for desc in cursor.description]
                    sucursalesData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
                
                udcConn.close()
            except Exception as e:
                return JsonResponse({'error': str(e)})

            context = {
                "usuarios": usuariosData,
                "sucursales": sucursalesData    
            }
            
            return render(request, 'token/config_tipos_token_solicitud.html', context) 


def new_tipo_token(request):

    user_name = request.session.get('userName', '')

    id_tipo = request.POST.get('id_tipo')
    new_tipo_token = request.POST.get('new_tipo_token')
    opcion = request.POST.get('opcion')

    try:
        udcConn = connections['udc_dev1']
        with udcConn.cursor() as cursor:
            cursor.callproc("CTRL_CREATE_TIPO_TOKEN", [id_tipo, new_tipo_token, user_name, opcion])
            results = cursor.fetchall()  
            if results:
                datos = {'save': 1, 'existe': results[0][0]}  
            else:
                datos = {'save': 1, 'existe': 0}
        
        udcConn.close()
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)


def get_select_tipo_token(request):

    opcion = request.POST.get('opcion')
    tokenData = ""

    try:
        udcConn = connections['udc_dev1']
        with udcConn.cursor() as cursor:

            cursor.callproc("CTRL_TIPOS_TOKEN_GET", [opcion])
            column_names = [desc[0] for desc in cursor.description]
            tokenData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        return JsonResponse({'data': tokenData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    
def get_usuarios_token(request):

    usuariosTokenData = ""

    try:
        udcConn = connections['udc_dev1']
        with udcConn.cursor() as cursor:

            cursor.callproc("CTRL_GET_USUARIOS_X_TIPO_TOKEN")
            column_names = [desc[0] for desc in cursor.description]
            usuariosTokenData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]
        
        udcConn.close()

        return JsonResponse({'data': usuariosTokenData})
    except Exception as e:
        return JsonResponse({'error': str(e)})
    

def add_usuarios_token(request):

    user_name = request.session.get('userName', '')

    tipo = request.POST.get('tipo')
    user_id = request.POST.get('user_id')

    try:
        udcConn = connections['udc_dev1']
        with udcConn.cursor() as cursor:
            cursor.callproc("CTRL_AGG_USER_TOKEN", [tipo, user_id, user_name])
            results = cursor.fetchall()  

            if results:
                datos = {'save': 1, 'existe': results[0][0]}  
            else:
                datos = {'save': 1, 'existe': 0}
        
        udcConn.close()
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)
    

def delete_usuarios_token(request):

    user_name = request.session.get('userName', '')
    id = request.POST.get('id')


    try:
        udcConn = connections['udc_dev1']
        with udcConn.cursor() as cursor:
            cursor.callproc("CTRL_REMOVE_USER_TOKEN", [id, user_name])
            results = cursor.fetchall()  

            datos = {'save': 1}
        
        udcConn.close()
    except Exception as e:
        datos = {'save': 0, 'error': str(e)}
    
    return JsonResponse(datos)


def get_listado_empleados(request):

    empleadosData = ""
    try:
        udcConn = connections['udc_dev1']
        with udcConn.cursor() as cursor:
            
            cursor.callproc("TH_GET_LISTADO_EMPLEADOS")
            column_names = [desc[0] for desc in cursor.description]
            empleadosData = [dict(zip(map(str, column_names), row)) for row in cursor.fetchall()]

        udcConn.close()

        return JsonResponse({'data': empleadosData})
    except Exception as e:
        return JsonResponse({'error': str(e)})