from django.urls import path
from .views import GlobalView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('panel/', GlobalView.global_main, name='global_main'),
    
    path('panel/modulos_usuario', GlobalView.global_modulos_usuario, name='global_modulos_usuario'),
    path('asignar_modulo', GlobalView.asignar_modulo, name="asignar_modulo"),
    path('quitar_modulo', GlobalView.quitar_modulo, name="quitar_modulo"),
    path('data_modulos_asignados', GlobalView.data_modulos_asignados, name='data_modulos_asignados'),
    path('data_modulos_disponibles', GlobalView.data_modulos_disponibles, name='data_modulos_disponibles'),

    path('panel/acciones_usuario', GlobalView.global_acciones_usuario, name='global_acciones_usuario'),
    path('asignar_accion', GlobalView.asignar_accion, name="asignar_accion"),
    path('quitar_accion', GlobalView.quitar_accion, name="quitar_accion"),
    path('data_acciones_asignadas', GlobalView.data_acciones_asignadas, name='data_acciones_asignadas'),
    path('data_acciones_disponibles', GlobalView.data_acciones_disponibles, name='data_acciones_disponibles'),

    path('panel/listado_usuario', GlobalView.global_listado_usuario, name='global_listado_usuario'),
    path('update_password_usuario', GlobalView.update_password_usuario, name='update_password_usuario'),
    path('update_nombrecompleto_usuario', GlobalView.update_nombrecompleto_usuario, name='update_nombrecompleto_usuario'),
    path('update_usuario_usuario', GlobalView.update_usuario_usuario, name='update_usuario_usuario'),
    path('update_estado_usuario', GlobalView.update_estado_usuario, name='update_estado_usuario'),
    path('data_usuarios_especial', GlobalView.data_usuarios_especial, name='data_usuarios_especial'),
    path('insert_usuario_listado', GlobalView.insert_usuario_listado, name='insert_usuario_listado'),
    path('obtener_contrasena', GlobalView.obtener_contrasena, name='obtener_contrasena'),
    path('obtener_historial_contraseña', GlobalView.obtener_historial_contraseña, name='obtener_historial_contraseña'),
    path('get_listado_empleados', GlobalView.get_listado_empleados, name='get_listado_empleados'),


    path('panel/grupos/admin_aplicaciones', GlobalView.global_admin_aplicaciones, name='global_admin_aplicaciones'),
    path('data_usuario_admin_disponibles', GlobalView.data_usuario_admin_disponibles, name='data_usuario_admin_disponibles'),
    path('data_usuario_admin_asignados', GlobalView.data_usuario_admin_asignados, name='data_usuario_admin_asignados'),
    path('asignar_usuarios_admin', GlobalView.asignar_usuarios_admin, name='asignar_usuarios_admin'),
    path('quitar_usuarios_admin', GlobalView.quitar_usuarios_admin, name='quitar_usuarios_admin'),

    path('panel/usuarios/grupo', GlobalView.global_usuarios_grupo, name='global_usuarios_grupo'),
    path('obtener_grupos_data', GlobalView.obtener_grupos_data, name='obtener_grupos_data'),
    path('data_usuario_grupo_asignado', GlobalView.data_usuario_grupo_asignado, name='data_usuario_grupo_asignado'),
    path('data_usuario_grupo_disponible', GlobalView.data_usuario_grupo_disponible, name='data_usuario_grupo_disponible'),
    path('asignar_usuario_grupo', GlobalView.asignar_usuario_grupo, name='asignar_usuario_grupo'),
    path('quitar_usuario_grupo', GlobalView.quitar_usuario_grupo, name='quitar_usuario_grupo'),

    path('panel/grupos/listado', GlobalView.global_listado_grupo, name='global_listado_grupo'),
    path('update_grupo', GlobalView.update_grupo, name='update_grupo'),
    path('insert_grupo', GlobalView.insert_grupo, name='insert_grupo'),
    path('delete_grupo', GlobalView.delete_grupo, name='delete_grupo'),

    path('panel/menus/listado', GlobalView.global_listado_menu, name='global_listado_menu'),
    path('obtener_menus_data', GlobalView.obtener_menus_data, name='obtener_menus_data'),
    path('insert_menu', GlobalView.insert_menu, name='insert_menu'),
    path('update_menu', GlobalView.update_menu, name='update_menu'),
    path('delete_menu', GlobalView.delete_menu, name='delete_menu'),
    path('update_estado_menu', GlobalView.update_estado_menu, name='update_estado_menu'),

    path('panel/grupos/usuario', GlobalView.global_grupos_usuario, name='global_grupos_usuario'),
    path('data_usuarios', GlobalView.data_usuarios, name='data_usuarios'),
    path('data_grupos_disponibles', GlobalView.data_grupos_disponibles, name='data_grupos_disponibles'),
    path('data_grupos_asignados', GlobalView.data_grupos_asignados, name='data_grupos_asignados'),
    path('insert_usuario_grupo', GlobalView.insert_usuario_grupo, name='insert_usuario_grupo'),
    path('eliminar_usuario_grupo', GlobalView.eliminar_usuario_grupo, name='eliminar_usuario_grupo'),

    path('panel/menus/usuario', GlobalView.global_menus_usuario, name='global_menus_usuario'),
    path('get_usuarios_menus_usuarios', GlobalView.get_usuarios_menus_usuarios, name='get_usuarios_menus_usuarios'),
    path('data_menus_disponibles', GlobalView.data_menus_disponibles, name='data_menus_disponibles'),
    path('data_grupos_usuarios_menus_usuarios', GlobalView.data_grupos_usuarios_menus_usuarios, name='data_grupos_usuarios_menus_usuarios'),
    path('data_menus_asignados', GlobalView.data_menus_asignados, name='data_menus_asignados'),
    path('data_menus_grupo', GlobalView.data_menus_grupo, name='data_menus_grupo'),
    path('data_menus_usuario', GlobalView.data_menus_usuario, name='data_menus_usuario'),
    path('delete_insert_menu_usuario', GlobalView.delete_insert_menu_usuario, name='delete_insert_menu_usuario'),
    path('delete_menus_usuario', GlobalView.delete_menus_usuario, name='delete_menus_usuario'),

    path('panel/admin/it', GlobalView.global_admin_it, name='global_admin_it'),
    path('get_modulos_admin_it', GlobalView.get_modulos_admin_it, name='get_modulos_admin_it'),
    path('get_usuarios_disponibles_admin_it_data', GlobalView.get_usuarios_disponibles_admin_it_data, name='get_usuarios_disponibles_admin_it_data'),
    path('get_usuarios_asignados_admin_it_data', GlobalView.get_usuarios_asignados_admin_it_data, name='get_usuarios_asignados_admin_it_data'),
    path('insert_usuario_it', GlobalView.insert_usuario_it, name='insert_usuario_it'),
    path('eliminar_usuario_it', GlobalView.eliminar_usuario_it, name='eliminar_usuario_it'),

    path('panel/menus/grupo', GlobalView.global_menus_grupo, name='global_menus_grupo'),
    path('get_menus_grupo_grupos_data', GlobalView.get_menus_grupo_grupos_data, name='get_menus_grupo_grupos_data'),
    path('get_menus_grupo_menus_data', GlobalView.get_menus_grupo_menus_data, name='get_menus_grupo_menus_data'),
    path('insert_delete_menu_grupo', GlobalView.insert_delete_menu_grupo, name='insert_delete_menu_grupo'),

    path('panel/acciones/grupo', GlobalView.global_acciones_grupo, name='global_acciones_grupo'),
    path('get_acciones_grupos_data', GlobalView.get_acciones_grupos_data, name='get_acciones_grupos_data'),
    path('get_acciones_grupos_diponibles_data', GlobalView.get_acciones_grupos_diponibles_data, name='get_acciones_grupos_diponibles_data'),
    path('get_acciones_grupos_asignadas_data', GlobalView.get_acciones_grupos_asignadas_data, name='get_acciones_grupos_asignadas_data'),
    path('insert_accion_grupo', GlobalView.insert_accion_grupo, name='insert_accion_grupo'),
    path('eliminar_accion_grupo', GlobalView.eliminar_accion_grupo, name='eliminar_accion_grupo'),

    path('panel/usuarios/autorizados/modulos', GlobalView.global_usuarios_autorizados_modulos, name='global_usuarios_autorizados_modulos'),
    path('get_usuarios_autorizados_modulos', GlobalView.get_usuarios_autorizados_modulos, name='get_usuarios_autorizados_modulos'),
    path('get_usuarios_autorizados_modulos_usuarios_disponibles_data', GlobalView.get_usuarios_autorizados_modulos_usuarios_disponibles_data, name='get_usuarios_autorizados_modulos_usuarios_disponibles_data'),
    path('get_usuarios_autorizados_modulos_usuarios_asignados_data', GlobalView.get_usuarios_autorizados_modulos_usuarios_asignados_data, name='get_usuarios_autorizados_modulos_usuarios_asignados_data'),
    path('insert_usuarios_autorizados_modulos_usuarios_disponible', GlobalView.insert_usuarios_autorizados_modulos_usuarios_disponible, name='insert_usuarios_autorizados_modulos_usuarios_disponible'),
    path('eliminar_usuarios_autorizados_modulos_usuarios_asignado', GlobalView.eliminar_usuarios_autorizados_modulos_usuarios_asignado, name='eliminar_usuarios_autorizados_modulos_usuarios_asignado'),


    path('panel/usuarios/sucursal', GlobalView.global_usuarios_de_la_sucursal, name='global_usuarios_de_la_sucursal'),
    path('get_usuarios_de_la_sucursal_sucursales_data', GlobalView.get_usuarios_de_la_sucursal_sucursales_data, name='get_usuarios_de_la_sucursal_sucursales_data'),
    path('get_usuarios_de_la_sucursal_usuarios_asignados_data', GlobalView.get_usuarios_de_la_sucursal_usuarios_asignados_data, name='get_usuarios_de_la_sucursal_usuarios_asignados_data'),
    path('get_usuarios_de_la_sucursal_usuarios_disponibles_data', GlobalView.get_usuarios_de_la_sucursal_usuarios_disponibles_data, name='get_usuarios_de_la_sucursal_usuarios_disponibles_data'),
    path('insert_usuarios_de_la_sucursal_usuarios_disponible', GlobalView.insert_usuarios_de_la_sucursal_usuarios_disponible, name='insert_usuarios_de_la_sucursal_usuarios_disponible'),
    path('eliminar_usuarios_de_la_sucursal_usuarios_asignado', GlobalView.eliminar_usuarios_de_la_sucursal_usuarios_asignado, name='eliminar_usuarios_de_la_sucursal_usuarios_asignado'),
    
    path('panel/sucursales/usuario', GlobalView.global_sucursales_del_usuario, name='global_sucursales_del_usuario'),
    path('get_sucursales_del_usuario_usuarios_data', GlobalView.get_sucursales_del_usuario_usuarios_data, name='get_sucursales_del_usuario_usuarios_data'),
    path('get_sucursales_del_usuario_sucursales_data', GlobalView.get_sucursales_del_usuario_sucursales_data, name='get_sucursales_del_usuario_sucursales_data'),
    path('get_sucursales_del_usuario_sucursales_asignadas_data', GlobalView.get_sucursales_del_usuario_sucursales_asignadas_data, name='get_sucursales_del_usuario_sucursales_asignadas_data'),
    path('get_sucursales_del_usuario_data', GlobalView.get_sucursales_del_usuario_data, name='get_sucursales_del_usuario_data'),
    path('insert_sucursales_del_usuario_sucursal_disponible', GlobalView.insert_sucursales_del_usuario_sucursal_disponible, name='insert_sucursales_del_usuario_sucursal_disponible'),
    path('eliminar_sucursales_del_usuario_sucursal_asignada', GlobalView.eliminar_sucursales_del_usuario_sucursal_asignada, name='eliminar_sucursales_del_usuario_sucursal_asignada'),
    
    path('panel/listado/acciones', GlobalView.global_listado_acciones, name='global_listado_acciones'),
    path('get_listado_acciones_data', GlobalView.get_listado_acciones_data, name='get_listado_acciones_data'),
    path('delete_accion', GlobalView.delete_accion, name='delete_accion'),
    path('update_accion', GlobalView.update_accion, name='update_accion'),
    path('create_accion', GlobalView.create_accion, name='create_accion'),

    path('panel/token', GlobalView.global_config_tipos_solicitud_tokens, name='global_config_tipos_solicitud_tokens'),
    path('new_tipo_token', GlobalView.new_tipo_token, name='new_tipo_token'),
    path('get_select_tipo_token', GlobalView.get_select_tipo_token, name='get_select_tipo_token'),
    path('get_usuarios_token', GlobalView.get_usuarios_token, name='get_usuarios_token'),
    path('add_usuarios_token', GlobalView.add_usuarios_token, name='add_usuarios_token'),
    path('delete_usuarios_token', GlobalView.delete_usuarios_token, name='delete_usuarios_token'),
    
]
