/**
 * Utilidades compartidas para el módulo de Activo Fijo
 */
const ActivoUtils = {
    // Formatea números a 2 decimales con separador de miles
    formatNumber: function (val) {
        return parseFloat(val || 0).toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    },

    // Retorna un el texto del estado con estilo badge
    getStatusBadge: function (status) {
        const states = {
            1: '<span class="badge bg-success">ACTIVO</span>',
            2: '<span class="badge bg-warning text-dark">INACTIVO</span>',
            3: '<span class="badge bg-danger">ELIMINADO</span>'
        };
        return states[parseInt(status)] || '<span class="badge bg-secondary">DESCONOCIDO</span>';
    },

    // Facilita las llamadas AJAX repetitivas
    ajax: function (url, data, successCb, type = 'GET') {
        $.ajax({
            url: url,
            type: type,
            data: data,
            success: successCb,
            error: (xhr) => {
                console.error("Error en API Activos:", xhr.responseText);
                alert("Error al procesar la solicitud.");
            }
        });
    }
};
