function mostrarCamposPorTipo(tipo) {
	var cuentaDiv = document.getElementById('campos-cuenta');
	var billeteraDiv = document.getElementById('campos-billetera');
	var tarjetaDiv = document.getElementById('campos-tarjeta');
	var chequeDiv = document.getElementById('campos-cheque');

	if (cuentaDiv) cuentaDiv.style.display = (tipo === 'cuenta_bancaria') ? '' : 'none';
	if (billeteraDiv) billeteraDiv.style.display = (tipo === 'billetera') ? '' : 'none';
	if (tarjetaDiv) tarjetaDiv.style.display = (tipo === 'tarjeta') ? '' : 'none';
	if (chequeDiv) chequeDiv.style.display = (tipo === 'cheque') ? '' : 'none';

	// Alternar required solo en los campos visibles
	var id_titular_cuenta = document.getElementById('id_titular_cuenta');
	var id_tipo_cuenta = document.getElementById('id_tipo_cuenta');
	var id_banco = document.getElementById('id_banco');
	var id_numero_cuenta = document.getElementById('id_numero_cuenta');
	var id_proveedor_billetera = document.getElementById('id_proveedor_billetera');
	var id_billetera_email_telefono = document.getElementById('id_billetera_email_telefono');
	var id_tarjeta_numero = document.getElementById('id_tarjeta_numero');
	var id_tarjeta_cvv = document.getElementById('id_tarjeta_cvv');
	var id_cheque_numero = document.getElementById('id_cheque_numero');

	if (id_titular_cuenta) id_titular_cuenta.required = (tipo === 'cuenta_bancaria');
	if (id_tipo_cuenta) id_tipo_cuenta.required = (tipo === 'cuenta_bancaria');
	if (id_banco) id_banco.required = (tipo === 'cuenta_bancaria');
	if (id_numero_cuenta) id_numero_cuenta.required = (tipo === 'cuenta_bancaria');
	if (id_proveedor_billetera) id_proveedor_billetera.required = (tipo === 'billetera');
	if (id_billetera_email_telefono) id_billetera_email_telefono.required = (tipo === 'billetera');
	if (id_tarjeta_numero) id_tarjeta_numero.required = (tipo === 'tarjeta');
	if (id_tarjeta_cvv) id_tarjeta_cvv.required = (tipo === 'tarjeta');
	if (id_cheque_numero) id_cheque_numero.required = (tipo === 'cheque');
}

document.addEventListener('DOMContentLoaded', function() {
	// Limitar número de tarjeta a 16 dígitos en tiempo real
	var tarjetaNumero = document.getElementById('id_tarjeta_numero');
	if (tarjetaNumero) {
		tarjetaNumero.addEventListener('input', function(e) {
			this.value = this.value.replace(/[^0-9]/g, '').slice(0, 16);
		});
	}
	// Ocultar el cuadro de error si no hay errores en los campos
	var errorBox = document.getElementById('error-box');
	var formInputs = document.querySelectorAll('form input, form select');
	formInputs.forEach(function(input) {
		input.addEventListener('input', function() {
			setTimeout(function() {
				if (!errorBox) return;
				// Mostrar si hay campos inválidos, ocultar si no
				if (document.querySelectorAll('.is-invalid').length > 0) {
					errorBox.style.display = '';
				} else {
					errorBox.style.display = 'none';
				}
			}, 200);
		});
	});
	// Ya no se restringe el campo de fecha, se usa el calendario nativo
	var selectTipo = document.getElementById('id_payment_type');
	if (selectTipo) {
		selectTipo.addEventListener('change', function() {
			mostrarCamposPorTipo(this.value);
		});
		mostrarCamposPorTipo(selectTipo.value);
	} else {
		// Si no hay select (estamos editando), buscar el input hidden
		var hiddenTipo = document.querySelector('input[name="payment_type"]');
		if (hiddenTipo) {
			mostrarCamposPorTipo(hiddenTipo.value);
		}
	}
	// Solo permitir números en número de tarjeta y CVV
	var tarjetaNumero = document.getElementById('id_tarjeta_numero');
	if (tarjetaNumero) {
		tarjetaNumero.addEventListener('input', function(e) {
			this.value = this.value.replace(/[^0-9]/g, '');
		});
	}
	var tarjetaCVV = document.getElementById('id_tarjeta_cvv');
	if (tarjetaCVV) {
		tarjetaCVV.addEventListener('input', function(e) {
			this.value = this.value.replace(/[^0-9]/g, '');
		});
	}
});
