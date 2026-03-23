from django.db import connections
from CONTABLE.views.utilsContable import _callproc_fetchall


def get_accesos_bancario(request):
    """
    Función utilitaria para refrescar los accesos (permisos) al entrar al módulo Bancario.
    Utiliza el id de módulo 1 según la base de datos global_security.menus.
    """
    user_id = request.session.get("user_id", "")
    if not user_id:
        return

    request.session["bancarioAdminIT"] = 0

    conn = connections["global_nube"]

    # 1) ¿Es admin IT del módulo Bancario?
    adminITQuery = _callproc_fetchall(conn, "WEB_GET_ADMIN_IT", [user_id, 1])
    if adminITQuery:
        request.session["bancarioAdminIT"] = 1

    # 2) Obtener los permisos del usuario para el módulo 1 (Bancario)
    menusBancario = _callproc_fetchall(
        conn, "WEB_GET_MENUS_GRUPO_USUARIO", [user_id, 1]
    )

    if menusBancario:
        for menu in menusBancario:
            posicion_menu = str(menu[2])
            permiso_menu = menu[6]
            request.session[posicion_menu] = 1 if permiso_menu == 1 else 0

            # Debug (opcional)
            # if permiso_menu == 1:
            #     print(f"{posicion_menu} PERMISO {permiso_menu}")


def verificar_acceso_bancario(request, posicion_menu):
    """
    Verifica si el usuario tiene acceso a la posición específica,
    ya sea por permiso explícito o porque es Admin IT de Bancario.
    Si no tiene acceso, devuelve una respuesta HTTP que redirige con el mensaje de error.
    Si sí tiene acceso, devuelve None.
    """
    from django.shortcuts import redirect

    if request.session.get("bancarioAdminIT", 0) == 1:
        return None

    if request.session.get(str(posicion_menu), 0) == 1:
        return None

    request.session["error_msg"] = "NO TIENES ACCESO"
    return redirect("panel_bancario")
