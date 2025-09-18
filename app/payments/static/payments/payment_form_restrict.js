    // Solo caracteres válidos para email o teléfono en billetera_email_telefono
    const emailTelInput = document.getElementById('id_billetera_email_telefono');
    if (emailTelInput) {
        emailTelInput.addEventListener('input', function(e) {
            let val = this.value;
            // Si solo números, limitar a 10 dígitos (no forzar 09)
            if (/^\d*$/.test(val)) {
                val = val.slice(0, 10);
                this.value = val;
            } else {
                // Permite letras, números, @, ., +, -, _
                const cursor = this.selectionStart;
                const original = this.value;
                const filtered = original.replace(/[^a-zA-Z0-9@.\-+_]/g, '');
                if (original !== filtered) {
                    this.value = filtered;
                    this.setSelectionRange(cursor - (original.length - filtered.length), cursor - (original.length - filtered.length));
                }
            }
        });
    }
    // Mostrar/ocultar campos según el tipo de método de pago
    function mostrarCamposPorTipo(tipo) {
        const tarjeta = document.getElementById('campos-tarjeta');
        const cuenta = document.getElementById('campos-cuenta');
        const billetera = document.getElementById('campos-billetera');
        if (tarjeta) tarjeta.style.display = (tipo === 'tarjeta') ? '' : 'none';
        if (cuenta) cuenta.style.display = (tipo === 'cuenta_bancaria') ? '' : 'none';
        if (billetera) billetera.style.display = (tipo === 'billetera') ? '' : 'none';
    }
    const selectTipo = document.getElementById('id_payment_type');
    if (selectTipo) {
        selectTipo.addEventListener('change', function() {
            mostrarCamposPorTipo(this.value);
        });
        // Mostrar campos correctos al cargar
        mostrarCamposPorTipo(selectTipo.value);
    }
// Validaciones centralizadas para métodos de pago
document.addEventListener('DOMContentLoaded', function() {
    // Limpiar guiones del número de tarjeta antes de enviar el formulario
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            const tarjetaNumero = document.getElementById('id_tarjeta_numero');
            if (tarjetaNumero) {
                tarjetaNumero.value = tarjetaNumero.value.replace(/[^0-9]/g, '');
            }
        });
    }
    // Solo números y máximo 16 dígitos para número de tarjeta, con guion cada 4 dígitos
    const tarjetaNumero = document.getElementById('id_tarjeta_numero');
    if (tarjetaNumero) {
        tarjetaNumero.addEventListener('input', function(e) {
            let val = this.value.replace(/[^0-9]/g, '').slice(0, 16);
            // Insertar guion cada 4 dígitos
            let formatted = '';
            for (let i = 0; i < val.length; i += 4) {
                if (i > 0) formatted += '-';
                formatted += val.substring(i, i + 4);
            }
            this.value = formatted;
        });
    }
    // Solo números y máximo 4 dígitos para CVV
    const tarjetaCVV = document.getElementById('id_tarjeta_cvv');
    if (tarjetaCVV) {
        tarjetaCVV.addEventListener('input', function(e) {
            let val = this.value.replace(/[^0-9]/g, '');
            if (val.length > 4) val = val.slice(0, 4);
            this.value = val;
        });
    }
    // Solo letras y espacios para nombres
    const nombreCampos = [
        document.getElementById('id_titular_cuenta'),
        document.getElementById('id_billetera_titular'),
        document.getElementById('id_tarjeta_nombre'),
        document.getElementById('id_tipo_cuenta'),
        document.getElementById('id_banco'),
        document.getElementById('id_tarjeta_marca'),
        document.getElementById('id_proveedor_billetera')
    ];
    nombreCampos.forEach(function(campo) {
        if (campo) {
            campo.addEventListener('input', function(e) {
                this.value = this.value.replace(/[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]/g, '');
            });
        }
    });
    // Solo números para número de cuenta (no borra todo, solo elimina caracteres prohibidos)
    const numeroCuenta = document.getElementById('id_numero_cuenta');
    if (numeroCuenta) {
        numeroCuenta.addEventListener('input', function(e) {
            const cursor = this.selectionStart;
            const original = this.value;
            const filtered = original.replace(/[^0-9]/g, '');
            if (original !== filtered) {
                this.value = filtered;
                // Restaurar posición del cursor si es posible
                this.setSelectionRange(cursor - (original.length - filtered.length), cursor - (original.length - filtered.length));
            }
        });
    }
    // Autoinsertar '/' en fecha de vencimiento y solo números
    const vencInput = document.getElementById('id_tarjeta_vencimiento');
    if (vencInput) {
        vencInput.addEventListener('input', function(e) {
            let val = this.value.replace(/[^0-9]/g, '');
            if (val.length > 2) {
                val = val.slice(0,2) + '/' + val.slice(2, 6);
            }
            this.value = val;
        });
    }
});
