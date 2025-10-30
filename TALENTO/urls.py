from django.urls import path
from .views import EmpleadosView, NominaView, AsistenciasView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Rutas principales
    path('talento/humano', EmpleadosView.vista_principal, name='modulos'),
    path('talento/humano/empleados', EmpleadosView.vista_principal_empleados, name='menu_empleados'),
    path('talento/humano/empleados/', EmpleadosView.vista_principal_empleados, name='ver_empleados'),

    # Ruta para crear un nuevo empleado
    path('talento/humano/empleados/gestion/new/', EmpleadosView.gestion_empleado, name='nuevo_empleado'),

    # Rutas para menús y obtención de datos
    path('menu-request/', EmpleadosView.menuRequest, name='menuRequest'),
    path('obtener_estados_empleados/', EmpleadosView.obtener_estados_empleados, name='obtener_estados_empleados'),
    path('talento/humano/empleados/gestion/obtener_info_empleado/', EmpleadosView.obtener_info_empleado, name='modulos'),
    path('guardar_documentos/', EmpleadosView.guardar_documentos, name='guardar_documentos'),
    path('empleados/informacion/', EmpleadosView.obtener_empleados_info, name='obtener_empleados_info'),
    path('talento/humano/empleados/gestion/obtener_datos_empleado/<int:id_empleado>/', EmpleadosView.obtener_datos_empleado, name='obtener_datos_empleado'),
    path('obtener_equipo_empleado/', EmpleadosView.obtener_equipo_empleado, name='obtener_equipo_empleado'),
    path('obtener_usuarios/', EmpleadosView.obtener_usuarios, name='obtener_usuarios'),
    path('obtener_contactos_familiar/', EmpleadosView.obtener_contactos_familiar, name='obtener_contactos_familiar'),
    path('obtener_posiciones/', EmpleadosView.obtener_posiciones, name='obtener_posiciones'),
    path('obtener-todos-tipos-curriculum/', EmpleadosView.obtener_todos_tipos_curriculum, name='obtener_todos_tipos_curriculum'),
    path('obtener_asociaciones/', EmpleadosView.obtener_asociaciones, name='obtener_asociaciones'),
    path('obtener_seguros/', EmpleadosView.obtener_seguros, name='obtener_seguros'),
    path('obtener_curriculums_por_empleado/', EmpleadosView.obtener_curriculums_por_empleado, name='obtener_curriculums_por_empleado'),
    path('obtener_contactos_emergencia/', EmpleadosView.obtener_contactos_emergencia, name='obtener_contactos_emergencia'),
    path('obtener_habilidades_empleado/<int:id_empleado>/', EmpleadosView.obtener_habilidades_empleado, name='obtener_habilidades_empleado'),
    path('obtener-estados/', EmpleadosView.obtener_estados_empleado_json, name='obtener_estados_empleado_json'),
    path('obtener_departamentos_por_pais/', EmpleadosView.obtener_departamentos_por_pais, name='obtener_departamentos_por_pais'),
    path('obtener_municipios_por_departamento/', EmpleadosView.obtener_municipios_por_departamento, name='obtener_municipios_por_departamento'),
    path('obtener_ciudades_por_municipio/', EmpleadosView.obtener_ciudades_por_municipio, name='obtener_ciudades_por_municipio'),
    path('obtener_barrios_por_ciudad/', EmpleadosView.obtener_barrios_por_ciudad, name='obtener_barrios_por_ciudad'),
    path('obtener_cargos_por_area/', EmpleadosView.obtener_cargos_por_area, name='obtener_cargos_por_area'),
    path('obtener_beneficio_laboral/', EmpleadosView.obtener_beneficio_laboral, name='obtener_beneficio_laboral'),
    path('obtener_beneficio_adicional/', EmpleadosView.obtener_beneficio_adicional, name='obtener_beneficio_adicional'),
    path('obtener_nacionalidades_por_pais/', EmpleadosView.obtener_nacionalidades_por_pais, name='obtener_nacionalidades_por_pais'),
    path('obtener_empleado_enfermedades_base/', EmpleadosView.obtener_empleado_enfermedades_base, name='obtener_empleado_enfermedades_base'),
    path('obtener_documentos_empleado/', EmpleadosView.obtener_documentos_empleado, name='obtener_documentos_empleado'),
    path('obtener_empleados_empresa/', EmpleadosView.obtener_empleados_empresa, name='obtener_empleados_empresa'),
    path('obtener_empleados_sucursal/', EmpleadosView.obtener_empleados_sucursal, name='obtener_empleados_sucursal'),
    path('obtener_empleados_departamento/', EmpleadosView.obtener_empleados_departamento, name='obtener_empleados_departamento'),
    path('obtener_empleados_cargo/', EmpleadosView.obtener_empleados_cargo, name='obtener_empleados_cargo'),
    path('obtener_empleados_area/', EmpleadosView.obtener_empleados_area, name='obtener_empleados_area'),
    path('obtener_empleados_rol/', EmpleadosView.obtener_empleados_rol, name='obtener_empleados_rol'),
    path('obtener_direccion_sucursal/', EmpleadosView.obtener_direccion_sucursal, name='obtener_direccion_sucursal'),
    path('obtener_bitacora_empleados/', EmpleadosView.obtener_bitacora_empleados, name='obtener_bitacora_empleados'),
 
    path('bitacora_empleado/<int:id_empleado>/', EmpleadosView.obtener_datos_X_bitacora_empleado, name='obtener_datos_X_bitacora_empleado'),
    path('vacaciones/', EmpleadosView.obtener_vacaciones, name='obtener_vacaciones'),
    path('vacaciones_dni/', EmpleadosView.obtener_vacaciones_por_dni, name='obtener_vacaciones_por_dni'),
    path('talento/humano/empleados/gestion/<parametro>', EmpleadosView.gestion_empleado, name='gestion_empleado'),
    path('talento/humano/empleados/gestion/insertar_identidad/', EmpleadosView.insertar_identidad, name='insertar_identidad'),
    path('talento/humano/empleados/gestion/actualizar_empleado/', EmpleadosView.actualizar_empleado, name='actualizar_empleado'),
    path('talento/humano/empleados/gestion/insertar_ficha_empleado/', EmpleadosView.insertar_ficha_empleado, name='insertar_ficha_empleado'),
    path('talento/humano/empleados/gestion/guardar_curriculum_empleado/', EmpleadosView.guardar_curriculum_empleado, name='guardar_curriculum_empleado'),
    path('talento/humano/empleados/gestion/guardar_equipos_empleado/', EmpleadosView.guardar_equipos_empleado, name='guardar_equipos_empleado'),

    path('actualizar_contrato/', EmpleadosView.actualizar_contrato, name='actualizar_contrato'),
    path('insertar-contacto-emergencia/', EmpleadosView.insertar_contacto_emergencia, name='insertar_contacto_emergencia'),
    path('insertar_contacto_emergencia/', EmpleadosView.insertar_contacto_emergencia, name='insertar_contacto_emergencia'),
    path('insertar_contacto_familiar/', EmpleadosView.insertar_contacto_familiar, name='insertar_contacto_familiar'),
    path('insertar_asociaciones_empleados/', EmpleadosView.insertar_asociaciones_empleados, name='insertar_asociaciones_empleados'),
    path('insertar_asociacion/', EmpleadosView.insertar_asociacion, name='insertar_asociacion'),
    path('insertar_seguros/', EmpleadosView.insertar_seguros, name='insertar_seguros'),
    path('insertar_beneficios_laborales/', EmpleadosView.insertar_beneficios_laborales, name='insertar_beneficios_laborales'),
    path('insertar_beneficio_adicional/', EmpleadosView.insertar_beneficio_adicional, name='insertar_beneficio_adicional'),
    path('insertar_parentesco/', EmpleadosView.insertar_parentesco, name='insertar_parentesco'),
    path('insertar_poliza_seguro/', EmpleadosView.insertar_poliza_seguro, name='insertar_poliza_seguro'),
    path('insertar_empresa_seguros/', EmpleadosView.insertar_empresa_seguros, name='insertar_empresa_seguros'),
    path('insertar_enfermedad_base/', EmpleadosView.insertar_enfermedad_base, name='insertar_enfermedad_base'),
    path('crear_rol_empleado/', EmpleadosView.crear_rol_empleado, name='crear_rol_empleado'),
    path('insertar_empleados_empresa/', EmpleadosView.insertar_empleados_empresa, name='insertar_empleados_empresa'),
    path('insertar_empleados_sucursal/', EmpleadosView.insertar_empleados_sucursal, name='insertar_empleados_sucursal'),
    path('insertar_empleados_departamentos/', EmpleadosView.insertar_empleados_departamentos, name='insertar_empleados_departamentos'),
    path('insertar_empleado_enfermedades_base/', EmpleadosView.insertar_empleado_enfermedades_base, name='insertar_empleado_enfermedades_base'),
    path('insertar_empleados_area/', EmpleadosView.insertar_empleados_area, name='insertar_empleados_area'),
    path('insertar_empleados_cargo/', EmpleadosView.insertar_empleados_cargo, name='insertar_empleados_cargo'),
    path('insertar_empleados_rol/', EmpleadosView.insertar_empleados_rol, name='insertar_empleados_rol'),


    # Rutas para crear datos
    path('crear_departamento/', EmpleadosView.crear_departamento, name='crear_departamento'),
    path('crear_certificaciones/', EmpleadosView.crear_certificaciones, name='crear_certificaciones'),
    path('crear_area/', EmpleadosView.crear_area, name='crear_area'),
    path('crear_tipo_cuenta/', EmpleadosView.crear_tipo_cuenta, name='crear_tipo_cuenta'),
    path('crear_contrato/', EmpleadosView.crear_contrato, name='crear_contrato'),
    path('crear_categoria_retiro/', EmpleadosView.crear_categoria_retiro, name='crear_categoria_retiro'),
    path('crear_motivo_retiro/', EmpleadosView.crear_motivo_retiro, name='crear_motivo_retiro'),
    path('crear_formas_pagos/', EmpleadosView.crear_formas_pagos, name='crear_formas_pagos'),
    path('crear_cargo/', EmpleadosView.crear_cargo, name='crear_cargo'),
    path('crear_habilidad/', EmpleadosView.crear_habilidad, name='crear_habilidad'),
    path('crear_posicion/', EmpleadosView.crear_posicion, name='crear_posicion'),
    path('crear_estado_empleado/', EmpleadosView.crear_estado_empleado, name='crear_estado_empleado'),
    path('crear_tipo_curriculum/', EmpleadosView.crear_tipo_curriculum, name='crear_tipo_curriculum'),
    path('crear_Equipo/', EmpleadosView.crear_Equipo, name='crear_Equipo'),
    path('crear_nuevo_banco/', EmpleadosView.crear_nuevo_banco, name='crear_nuevo_banco'),
    path('crear_nuevo_beneficio_laboral/', EmpleadosView.crear_nuevo_beneficio_laboral, name='crear_nuevo_beneficio_laboral'),
    path('crear_nuevo_beneficio_adicional/', EmpleadosView.crear_nuevo_beneficio_adicional, name='crear_nuevo_beneficio_adicional'),
    path('agregar_habilidad_empleado/', EmpleadosView.agregar_habilidad_empleado, name='agregar_habilidad_empleado'),
    path('crear_pais/', EmpleadosView.crear_pais, name='crear_pais'),
    path('crear_departamento_pais/', EmpleadosView.crear_departamento_pais, name='crear_departamento_pais'),
    path('crear_municipio/', EmpleadosView.crear_municipio, name='crear_municipio'),
    path('crear_barrio_colonia/', EmpleadosView.crear_barrio_colonia, name='crear_barrio_colonia'),
    path('crear_ciudad/', EmpleadosView.crear_ciudad, name='crear_ciudad'),
    path('crear_profesion_oficio/', EmpleadosView.crear_profesion_oficio, name='crear_profesion_oficio'),
    path('crear_centro_educativo/', EmpleadosView.crear_centro_educativo, name='crear_centro_educativo'),
    path('crear_cat_equipo/', EmpleadosView.crear_cat_equipo, name='crear_cat_equipo'),
    path('crear_nuevo_tipo_curriculum/', EmpleadosView.crear_nuevo_tipo_curriculum, name='crear_nuevo_tipo_curriculum'),

    # Rutas adicionales
    path('guardar_usuario/', EmpleadosView.guardar_usuario, name='guardar_usuario'),
    path('guardar_ficha_empleado/', EmpleadosView.guardar_ficha_empleado, name='guardar_ficha_empleado'),

    #Rutas para actualizar datos
    path('actualizar_curriculum_empleado/', EmpleadosView.actualizar_curriculum_empleado, name='actualizar_curriculum_empleado'),
    path('actualizar_contacto_familiar/', EmpleadosView.actualizar_contacto_familiar, name='actualizar_contacto_familiar'),
    path('desactivar_familiar/', EmpleadosView.desactivar_familiar, name='desactivar_familiar'),
    path('eliminar_beneficio_laboral/', EmpleadosView.eliminar_beneficio_laboral, name='eliminar_beneficio_laboral'),
    path('eliminar_beneficio_adicional/', EmpleadosView.eliminar_beneficio_adicional, name='eliminar_beneficio_adicional'),

    path('filtrar-subgrupos/', EmpleadosView.filtrar_subgrupos_por_grupo, name='filtrar_subgrupos_por_grupo'),
    path('contar_empleados/', EmpleadosView.contar_empleados, name='contar_empleados'),
    path('validar_contrato/', EmpleadosView.validar_contrato, name='validar_contrato'),
    path('check_session/', EmpleadosView.check_session, name='check_session'),
    path('get_info_menu/', EmpleadosView.get_info_menu, name='get_info_menu'),

    #Nomina
    path('talento/humano/nomina/', NominaView.nueva_planilla, name='nueva_planilla'),
    path('talento/humano/gestion-planilla/', NominaView.gestion_planilla, name='gestion_planilla'),
    path('mostrar_tipos_deducciones/', NominaView.mostrar_tipos_deducciones, name='mostrar_tipos_deducciones'),
    path('guardar_tipo_deduccion/', NominaView.guardar_tipo_deduccion, name='guardar_tipo_deduccion'),
    path('mostrar_tipos_deduccion_banco/', NominaView.mostrar_tipos_deduccion_banco, name='mostrar_tipos_deduccion_banco'),
    path('obtener_cat_categorias_tipos_deduccion/', NominaView.obtener_cat_categorias_tipos_deduccion, name='obtener_cat_categorias_tipos_deduccion'),
    
    #insertar planilla
    path('insertar_planilla/', NominaView.insertar_planilla, name='insertar_planilla'),
    path('actualizar_automatico_manual/', NominaView.actualizar_automatico_manual, name='actualizar_automatico_manual'),
    path('obtener_planillas/', NominaView.obtener_planillas, name='obtener_planillas'),
    path('obtener_detalles_planilla/', NominaView.obtener_detalles_planilla, name='obtener_detalles_planilla'),
    path('obtener_detalles_planilla_v2', NominaView.obtener_detalles_planilla_v2, name='obtener_detalles_planilla_v2'),
    path('obtener_bonificaciones/', NominaView.obtener_bonificaciones, name='obtener_bonificaciones'),
    path('obtener_deducciones_por_empleado/', NominaView.obtener_deducciones_por_empleado, name='obtener_deducciones_por_empleado'),
    path('obtener_codigos_planillas/', NominaView.obtener_codigos_planillas, name='obtener_codigos_planillas'),
    path('obtener_bonificaciones_por_empleado/', NominaView.obtener_bonificaciones_por_empleado, name='obtener_bonificaciones_por_empleado'),
    path('subir_deducciones_bonificaciones/', NominaView.subir_deducciones_bonificaciones, name='subir_deducciones_bonificaciones'),
    path('obtener_empleados/', NominaView.obtener_empleados, name='obtener_empleados'),
    path('insertar_deduccion_manual/', NominaView.insertar_deduccion_manual, name='insertar_deduccion_manual'),
    path('insertar_bonificacion_manual/', NominaView.insertar_bonificacion_manual, name='insertar_bonificacion_manual'),
    path('mostrar_tipos_bonificaciones/', NominaView.mostrar_tipos_bonificaciones, name='mostrar_tipos_bonificaciones'),
    path('mostrar_tipos_Comisiones/', NominaView.mostrar_tipos_Comisiones, name='mostrar_tipos_Comisiones'),
    path('guardar_tipo_bonificacion/', NominaView.guardar_tipo_bonificacion, name='guardar_tipo_bonificacion'),
    path('guardar_tipo_Comisiones/', NominaView.guardar_tipo_Comisiones, name='guardar_tipo_Comisiones'),
    path('aplicar_planilla/', NominaView.aplicar_planilla, name='aplicar_planilla'),
    path('eliminar_planilla/', NominaView.eliminar_planilla, name='eliminar_planilla'),
    path('eliminar_deduccion/', NominaView.eliminar_deduccion, name='eliminar_deduccion'),
    path('editar_deduccion/', NominaView.editar_deduccion, name='editar_deduccion'),
    path('eliminar_tipo_deduccion/', NominaView.eliminar_tipo_deduccion, name='eliminar_tipo_deduccion'),
    path('eliminar_tipo_bonificacion/', NominaView.eliminar_tipo_bonificacion, name='eliminar_tipo_bonificacion'),
    path('eliminar_tipo_Comision/', NominaView.eliminar_tipo_Comision, name='eliminar_tipo_Comision'),
    path('insertar_categoria_deduccion/', NominaView.insertar_categoria_deduccion, name='insertar_categoria_deduccion'),
    path('insertar_bonificacion_tipo/', NominaView.insertar_bonificacion_tipo, name='insertar_bonificacion_tipo'),
    path('insertar_tipo_deduccion_banco/', NominaView.insertar_tipo_deduccion_banco, name='insertar_tipo_deduccion_banco'),
    path('obtener_detalles_planilla_no_asociados/', NominaView.obtener_detalles_planilla_no_asociados, name='obtener_detalles_planilla_no_asociados'),
    path('obtener_tipos_archivo/', NominaView.obtener_tipos_archivo, name='obtener_tipos_archivo'),
    path('obtener_tipos_manuales/', NominaView.obtener_tipos_manuales, name='obtener_tipos_manuales'),
    path('eliminar_empleados_no_asociados/', NominaView.eliminar_empleados_no_asociados, name='eliminar_empleados_no_asociados'),
    path('actualizar_detalle_planilla_no_asociada/', NominaView.actualizar_detalle_planilla_no_asociada, name='actualizar_detalle_planilla_no_asociada'),
    path('get_detalles_x_empleado/', NominaView.get_detalles_x_empleado, name='get_detalles_x_empleado'),
    path('verificar_registros_deducciones/', NominaView.verificar_registros_deducciones, name='verificar_registros_deducciones'),
    
    path('eliminar_deduccion_x_empleado/', NominaView.eliminar_deduccion_x_empleado, name='eliminar_deduccion_x_empleado'),
   
    #Bonificaciones y deducciones
    path('talento/humano/nomina/deducciones', NominaView.nueva_deduccion, name='nueva_deduccion'),
    path('talento/humano/nomina/bonificaciones', NominaView.nueva_bonificacion, name='nueva_bonificacion'),
    path('talento/humano/nomina/comision', NominaView.nueva_comision, name='nueva_comision'),
    path('talento/humano/nomina/reportes', NominaView.reportes, name='reportes'),
    path('comprobante_bancos', NominaView.comprobante_bancos, name='comprobante_bancos'),
    path('reporte_deducciones', NominaView.reporte_deducciones, name='reporte_deducciones'),


    path('aplicar_nueva_fecha_por_aplicar_planilla', NominaView.aplicar_nueva_fecha_por_aplicar_planilla, name='aplicar_nueva_fecha_por_aplicar_planilla'),
    path('set_new_fecha_aplicar_planilla', NominaView.set_new_fecha_aplicar_planilla, name='set_new_fecha_aplicar_planilla'),
    path('desaplicar_planilla', NominaView.desaplicar_planilla, name='desaplicar_planilla'),
    path('registrar_saldos_empleados_planillas', NominaView.registrar_saldos_empleados_planillas, name='registrar_saldos_empleados_planillas'),
    path('aplica_salario_completo', NominaView.aplica_salario_completo, name='aplica_salario_completo'),
    path('validar_fecha_aplicar_planilla', NominaView.validar_fecha_aplicar_planilla, name='validar_fecha_aplicar_planilla'),


    #Modulos de Talento Humano
    path('talento/humano', AsistenciasView.vista_principal_modulos, name='vista_principal_modulos'),



    #Asistencia de empleados 
    path('talento/humano/asistencias', AsistenciasView.nueva_asistencia, name='nueva_asistencia'),

    #Horarios
    path('talento/humano/nomina/asistencia/horarios', AsistenciasView.horarios, name='horarios'),
    path('talento/humano/nomina/asistencia/registros', AsistenciasView.registro, name='tipo_registro'),
    path('talento/humano/nomina/asistencia/departamentos', AsistenciasView.departamentos_turnos, name='departamentos_turnos'),
    path('talento/humano/nomina/asistencia/dias/libres', AsistenciasView.dias_libres_turnos, name='dias_libres_turnos'),
    path('talento/humano/nomina/asistencia/incidencias', AsistenciasView.incidencias, name='incidencias'),
    path('mostrar_asistencia_marcados', AsistenciasView.mostrar_asistencia_marcados, name='mostrar_asistencia_marcados'),

    path('mostrar_departamentos_empresa', AsistenciasView.mostrar_departamentos_empresa, name='mostrar_departamentos_empresa'),
    path('insert_update_turno', AsistenciasView.insert_update_turno, name='insert_update_turno'),
    path('update_status_turno', AsistenciasView.update_status_turno, name='update_status_turno'),
    path('get_horarios_x_turno', AsistenciasView.get_horarios_x_turno, name='get_horarios_x_turno'),
    path('update_dia_libre_horarios', AsistenciasView.update_dia_libre_horarios, name='update_dia_libre_horarios'),
    path('update_horas_x_dia_x_horario', AsistenciasView.update_horas_x_dia_x_horario, name='update_horas_x_dia_x_horario'),
    path('mostrar_turnos', AsistenciasView.mostrar_turnos, name='mostrar_turnos'),
    path('export_and_import_data', AsistenciasView.export_and_import_data, name='export_and_import_data'),
    path('obtener_empleado_departamento', AsistenciasView.obtener_empleado_departamento, name='obtener_empleado_departamento'),
    path('actualizar_empleado_departamento', AsistenciasView.actualizar_empleado_departamento, name='actualizar_empleado_departamento'),
    path('mostrar_turnos_empleados', AsistenciasView.mostrar_turnos_empleados, name='mostrar_turnos_empleados'),
    path('insertar_incidencias_registradas', AsistenciasView.insertar_incidencias_registradas, name='insertar_incidencias_registradas'),
    path('mostrar_todas_incidencias', AsistenciasView.mostrar_todas_incidencias, name='mostrar_todas_incidencias'),
    path('insert_update_tipo_incidencia', AsistenciasView.insert_update_tipo_incidencia, name='insert_update_tipo_incidencia'),
    path('update_status_incidencia', AsistenciasView.update_status_incidencia, name='update_status_incidencia'),



    path('verificar_acceso', EmpleadosView.verificar_acceso, name='verificar_acceso'),
    path('insertar_registro_incendincias_manual', AsistenciasView.insertar_registro_incendincias_manual, name='insertar_registro_incendincias_manual'),
    path('mostrar_dias_libres', AsistenciasView.mostrar_dias_libres, name='mostrar_dias_libres'),
    path('mostrar_todos_turnos', AsistenciasView.mostrar_todos_turnos, name='mostrar_todos_turnos'),
    path('eliminar_dia_libre', AsistenciasView.eliminar_dia_libre, name='eliminar_dia_libre'),

    path('insertar_dias_libres_turnos', AsistenciasView.insertar_dias_libres_turnos, name='insertar_dias_libres_turnos'),
    path('actualizar_dias_libres_turnos', AsistenciasView.actualizar_dias_libres_turnos, name='actualizar_dias_libres_turnos'),
]

# Añadir rutas para servir archivos estáticos y de medios en modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
