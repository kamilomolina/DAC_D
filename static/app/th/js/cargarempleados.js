
    function cargarEstadosEmpleados() {
        $.ajax({
            url: '/CWS/modulos/talento/humano/empleados/gestion/obtener_info_empleado/',
            type: 'GET',
            success: function (response) {
                console.log('Response:', response); // Añadir mensaje de depuración

                if (response.status === 'success') {
                    var empleadosContainer = $('#empleados-container');
                    empleadosContainer.empty(); // Limpiar el contenedor antes de agregar nuevos elementos

                    response.data.forEach(function (empleado) {
                        var estadoIcono;
                        switch (empleado.estado) {
                            case 1:
                                estadoIcono = '<i class="fas fa-circle text-success"></i>';
                                break;
                            case 3:
                                estadoIcono = '<i class="fas fa-circle text-danger"></i>';
                                break;
                            default:
                                estadoIcono = '<i class="fas fa-circle text-secondary"></i>'; // Icono por defecto para otros estados
                                break;
                        }

                        var empleadoImagen;
                        if (empleado.imagen) {
                            empleadoImagen = `<img src="/media/${empleado.imagen}" class="img-thumbnail" style="width: 80px; height: 80px;">`;
                        } else {
                            var initial = empleado.nombre_completo.charAt(0);
                            empleadoImagen = `
                                <div class="bg-success text-white d-flex justify-content-center align-items-center"
                                    style="width: 80px; height: 80px; font-size: 1.5rem;">
                                    ${initial}
                                </div>
                            `;
                        }

                        var tarjetaEmpleado = `
                            <div class="col-md-3 col-sm-4 mb-2">
                                <div class="card h-100 card-empleado" id="${empleado.id_empleado}">
                                    <div class="card-body d-flex">
                                        <div class="me-3">
                                            ${empleadoImagen}
                                        </div>
                                        <div class="flex-grow-1">
                                            <h6 class="card-title mb-1">${empleado.nombre_completo}</h6>
                                            <p class="card-text mb-1" style="font-size: 0.75rem;"><i class="fas fa-envelope"></i> ${empleado.correo}</p>
                                            <p class="card-text mb-1" style="font-size: 0.75rem;"><i class="fas fa-phone"></i> ${empleado.telefono}</p>
                                            <p class="card-text mb-1" style="font-size: 0.75rem;">${estadoIcono}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                        empleadosContainer.append(tarjetaEmpleado);
                    });

                    // Delegación de eventos para manejar clics en tarjetas dinámicamente generadas
                    $(document).on('click', '.card-empleado', function () {
                        var idEmpleado = this.id;
                        console.log("ID Empleado: " + idEmpleado);
                        window.location.href = `/CWS/modulos/talento/humano/empleados/gestion/` + idEmpleado;
                    });
                } else {
                    console.error('Error:', response.error); // Añadir mensaje de depuración
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'Error al obtener los estados de los empleados: ' + response.error,
                    });
                }
            },
            error: function (response) {
                console.error('Error en la solicitud:', response.responseText); // Añadir mensaje de depuración
                Swal.fire({
                    icon: 'error',
                    title: 'Error en la solicitud',
                    text: 'Error en la solicitud: ' + response.responseText,
                });
            }
        });
    }


    $(document).ready(function () {
        cargarEstadosEmpleados(); // Cargar los datos cuando la página esté lista
    });
