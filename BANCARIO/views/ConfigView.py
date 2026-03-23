import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.db import connections
from CONTABLE.views.utilsContable import getUsers

from BANCARIO.views.utilsBancario import *


def bancario_config_destinos_procedencias(request):
    user_id = request.session.get("user_id", "")
    adminIT = int(request.session.get("ctrlGestionAdminIT", 0))

    if user_id == "":
        return HttpResponseRedirect(reverse("login"))

    acceso_denegado = verificar_acceso_bancario(request, "40110")
    if acceso_denegado:
        return acceso_denegado

    usersData = getUsers()

    context = {
        "usersData": usersData,
        "adminIT": adminIT,
    }

    return render(request, "configuraciones/destinos_procedencias.html", context)


def bk_get_lista_asignaciones(request):
    if request.method == "POST":
        pUsuario = int(request.POST.get("usuario_id", 0))
        pTipo = int(request.POST.get("tipo", 1))

        if pUsuario == 0:
            return JsonResponse({"success": False, "msg": "Usuario no válido."})

        try:
            with connections["bankConn"].cursor() as cursor:
                cursor.callproc("BK_GET_TODOS_CON_ASIGNACION", [pUsuario, pTipo])
                column_names = [desc[0] for desc in cursor.description]
                data = [dict(zip(column_names, row)) for row in cursor.fetchall()]

            return JsonResponse({"success": True, "data": data})
        except Exception as e:
            return JsonResponse({"success": False, "msg": str(e)})

    return JsonResponse({"success": False, "msg": "Método no permitido."})


def bk_toggle_asignacion(request):
    if request.method == "POST":
        pUsuario = int(request.POST.get("usuario_id", 0))
        pTipo = int(request.POST.get("tipo", 1))
        pFkRegistro = int(request.POST.get("registro_id", 0))
        accion = request.POST.get("accion", "")
        pCreadoPor = request.session.get("userName", "system")

        if pUsuario == 0 or pFkRegistro == 0:
            return JsonResponse({"success": False, "msg": "Parámetros inválidos."})

        try:
            with connections["bankConn"].cursor() as cursor:
                if accion == "add":
                    cursor.callproc(
                        "BK_SET_USUARIO_DESTINO_PROCEDENCIA",
                        [pUsuario, pTipo, pFkRegistro, pCreadoPor],
                    )
                elif accion == "remove":
                    cursor.callproc(
                        "BK_DEL_USUARIO_DESTINO_PROCEDENCIA",
                        [pUsuario, pTipo, pFkRegistro],
                    )
                else:
                    return JsonResponse({"success": False, "msg": "Acción inválida."})

            return JsonResponse(
                {"success": True, "msg": "Asignación actualizada correctamente."}
            )
        except Exception as e:
            return JsonResponse({"success": False, "msg": str(e)})

    return JsonResponse({"success": False, "msg": "Método no permitido."})
