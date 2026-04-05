/**
 * Utilidades compartidas para el módulo de Activo Fijo
 * Versión 1.3 - Definición Global Robusta
 */
(function(window) {
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
                3: '<span class="badge bg-danger">ELIMINADO</span>',
                'ACTIVO': '<span class="badge bg-success">ACTIVO</span>',
                'INACTIVO': '<span class="badge bg-warning text-dark">INACTIVO</span>'
            };
            return states[status] || states[parseInt(status)] || '<span class="badge bg-secondary">DESCONOCIDO</span>';
        },

        /**
         * Obtiene el valor de una propiedad sin importar si es mayúscula, minúscula o camello
         * Muy útil con drivers de BD que retornan distintos formatos
         */
        getVal: function (obj, key, defaultVal = '') {
            if (!obj) return defaultVal;
            
            const lowerKey = key.toLowerCase();
            const upperKey = key.toUpperCase();
            
            if (obj.hasOwnProperty(key)) return obj[key] ?? defaultVal;
            if (obj.hasOwnProperty(lowerKey)) return obj[lowerKey] ?? defaultVal;
            if (obj.hasOwnProperty(upperKey)) return obj[upperKey] ?? defaultVal;
            
            // Búsqueda insensible a mayúsculas
            for (let k in obj) {
                if (k.toLowerCase() === lowerKey) return obj[k] ?? defaultVal;
            }
            
            return defaultVal;
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
                    // No alertamos para evitar spam si hay muchos errores de carga
                    console.warn("No se pudo completar la petición AJAX a: " + url);
                }
            });
        }
    };

    // Exportar al objeto window para acceso global
    window.ActivoUtils = ActivoUtils;
})(window);
