console.log('hola desde el menu');

function handleIconClick() {
    window.history.back();
}

$(document).ready(function () {
    $(".formattedMoneyInputs").inputmask("decimal", {
        radixPoint: ".",
        groupSeparator: ",",
        digits: 2,
        autoGroup: true,
        rightAlign: false,
        removeMaskOnSubmit: true,
    });

    // Inicializar Select2
    $('#mySelect2').select2();

    // Evento para abrir el modal
    $('#mySelect2').on('select2:select', function (e) {
        $('#myModal').modal('show');
    });

    // Llamar modal Departamentos
    document.getElementById('linkDepartamentos').addEventListener('click', function (event) {
        event.preventDefault(); // Evitar el comportamiento predeterminado del enlace
        var modal = new bootstrap.Modal(document.getElementById('modalCrearDepartamento'));
        modal.show();
    });

    // Llamar modal Área
    document.getElementById('linkAreas').addEventListener('click', function (event) {
        event.preventDefault(); // Evitar el comportamiento predeterminado del enlace
        var modalArea = new bootstrap.Modal(document.getElementById('modalCrearArea'));
        modalArea.show();
    });

    // Llamar modal Cargo
    document.getElementById('linkCargos').addEventListener('click', function (event) {
        event.preventDefault(); // Evitar el comportamiento predeterminado del enlace
        var modalCargo = new bootstrap.Modal(document.getElementById('modalCrearCargo'));
        modalCargo.show();
    });

    // Llamar modal Posición
    document.getElementById('linkPosiciones').addEventListener('click', function (event) {
        event.preventDefault(); // Evitar el comportamiento predeterminado del enlace
        var modalPosicion = new bootstrap.Modal(document.getElementById('modalCrearPosicion'));
        modalPosicion.show();
    });

    // Llamar modal Categoría de Retiro
    document.getElementById('linkCatRetiro').addEventListener('click', function (event) {
        event.preventDefault(); // Evitar el comportamiento predeterminado del enlace
        var modalCatRetiro = new bootstrap.Modal(document.getElementById('modalCrearCatRetiro'));
        modalCatRetiro.show();
    });

    // Llamar modal Tipo de Contrato
    document.getElementById('linkTipoContrato').addEventListener('click', function (event) {
        event.preventDefault(); // Evitar el comportamiento predeterminado del enlace
        var modalTipoContrato = new bootstrap.Modal(document.getElementById('modalCrearTipoContrato'));
        modalTipoContrato.show();
    });

    // Llamar modal Currículum
    document.getElementById('linkCurriculum').addEventListener('click', function (event) {
        event.preventDefault(); // Evitar el comportamiento predeterminado del enlace
        var modalCurriculum = new bootstrap.Modal(document.getElementById('modalCurriculum'));
        modalCurriculum.show();
    });

    // Cambiar en las opciones del select departamentos
    $('#departamento').on('change', function () {
        var selectedValue = $(this).val();
        console.log('Select changed:', selectedValue); // Verificar el valor seleccionado
        if (selectedValue === 'new-department') {
            console.log('Opening modal for new department'); // Verificar la condición
            $('#modalCrearDepartamento').modal('show'); // Mostrar el modal
            $(this).val(''); // Restablecer el valor del select
        }
    });

    // Crear Departamentos
    $('#formCrearDepartamento').on('submit', function (event) {
        event.preventDefault(); // Prevenir el envío del formulario

        var nuevoDepartamento = $('#nuevoDepartamento').val();
        var creadoPor = $('#usuario').val();
        console.log(creadoPor);

        $.ajax({
            url: urlCrearDepartamento,
            type: 'POST',
            data: {
                departamento: nuevoDepartamento,
                creado_por: creadoPor,
                csrfmiddlewaretoken: csrfToken
            },
            success: function (response) {
                if (response.status === 'success') {
                    $('#modalCrearDepartamento').modal('hide');

                    Swal.fire({
                        icon: 'success',
                        title: 'Departamento creado exitosamente',
                        text: 'El Departamento ha sido guardado exitosamente.',
                        showConfirmButton: false,
                        timer: 1500
                    });
                    obtenerDepartamentos();
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error',
                        text: 'Error al crear el departamento: ' + response.error,
                    });
                }
            },
            error: function (xhr, status, error) {
                alert('Error en la solicitud: ' + error);
            }
        });
    });

    // Obtener departamentos
    function obtenerDepartamentos() {
        $.ajax({
            url: urlObtenerDepartamentos,
            type: 'GET',
            success: function (response) {
                if (response.status === 'success') {
                    var select = $('#departamento');
                    select.empty();
                    select.append('<option value="">Seleccione un departamento</option>');
                    select.append('<option value="new-department">Crear nuevo departamento</option>');
                    response.departamentos.forEach(function (departamento) {
                        select.append('<option value="' + departamento.id + '">' + departamento.nombre + '</option>');
                    });
                } else {
                    alert('Error al obtener la lista de departamentos: ' + response.error);
                }
            },
            error: function (xhr, status, error) {
                alert('Error en la solicitud: ' + error);
            }
        });
    }
});
