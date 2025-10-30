from django.urls import path
from . import views


urlpatterns = [

    path('lobby/', views.vista_principal_lobby, name='kanban_lobby'),  
    path('', views.vista_principal_kanban, name='kanban_principal'),  
    path('planes/', views.obtener_planes_usuario, name='obtener_planes_usuario'),
    path('gestion-planes/', views.gestion_planes, name='gestion_planes'),
    path('actualizar_estado_plan/', views.actualizar_estado_plan, name='actualizar_estado_plan'),
    path('crear_actualizar_columnas/', views.crear_actualizar_columnas, name='crear_actualizar_columnas'),
    path('crear_tarea/', views.crear_tarea, name='crear_tarea'),
    path('obtener_columnas_plan/', views.obtener_columnas_plan, name='obtener_columnas_plan'),
    path('detalle_plan/<int:id_plan>/', views.detalle_plan, name='detalle_plan'),
    path('obtener_detalles_tarea/', views.obtener_detalles_tarea, name='obtener_detalles_tarea'),
    path('obtener_estados_plan/<int:id_plan>/', views.obtener_estados_plan, name='obtener_estados_plan'),
    path('obtener-tareas/<int:id_columna>/', views.obtener_tareas_por_columna, name='obtener_tareas_por_columna'),
    path('knb_tasks_update/', views.knb_tasks_update, name='knb_tasks_update'),
    path('knb_tasks_details_create_update/', views.knb_tasks_details_create_update, name='knb_tasks_details_create_update'),
    path('obtener-detalles-tarea/<int:tarea_id>/', views.obtener_detalles_tarea, name='obtener_detalles_tarea'),
    path('agregar_usuario_a_plan/', views.agregar_usuario_a_plan, name='agregar_usuario_a_plan'),
    path('get_plant_metrics_percentages/', views.get_plant_metrics_percentages, name='get_plant_metrics_percentages'),
    path('miembros_plan/<int:plan_id>/', views.obtener_miembros_plan, name='obtener_miembros_plan'),
    path('planes/<int:plan_id>/', views.obtener_datos_plan, name='obtener_datos_plan'),
    path('actualizar-tarea-columna/', views.actualizar_tarea_columna, name='actualizar_tarea_columna'),
    path('ver_detalle_tarea/', views.ver_detalle_tarea, name='ver_detalle_tarea'),
    path('eliminar-columna/', views.eliminar_columna, name='eliminar_columna'),
    path('eliminar-tarea/', views.eliminar_tarea, name='eliminar_tarea'),
    path('eliminar-plan/', views.eliminar_plan, name='eliminar_plan'),
    path('validar_plan_completo/', views.validar_plan_completo, name='validar_plan_completo'),
    path('create_update_comentario/', views.create_update_comentario, name='create_update_comentario'),
    path('update_estado_plan/', views.update_estado_plan, name='update_estado_plan'),
    path('update_task_completed/', views.update_task_completed, name='update_task_completed'),
    path('desactivar_tarea/', views.desactivar_tarea, name='desactivar_tarea'),





]