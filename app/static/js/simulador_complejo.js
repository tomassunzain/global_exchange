// --- Variables globales y carga de datos ---
let comisiones = [];
// Carga el archivo de comisiones.json y lo almacena en la variable global 'comisiones'
async function cargarComisiones() {
	try {
		const resp = await fetch('/static/comisiones.json');
		if (!resp.ok) throw new Error('No se pudo obtener comisiones');
		comisiones = await resp.json();
	} catch (e) {
		mostrarError('Error al cargar comisiones: ' + e.message);
	}
}
// Obtiene el segmento (tipo) del cliente activo seleccionado en el dashboard
function obtenerSegmentoClienteActivo() {
	const form = document.getElementById('form-cliente-activo');
	if (!form) return 'MIN'; // fallback minorista
	const select = form.querySelector('select[name="cliente_id"]');
	if (!select) return 'MIN';
	const selectedOption = select.options[select.selectedIndex];
	if (!selectedOption) return 'MIN';
	const match = selectedOption.textContent.match(/\(([^)]+)\)/);
	if (!match) return 'MIN';
	const tipo = match[1].toUpperCase();
	if (tipo.startsWith('VIP')) return 'VIP';
	if (tipo.startsWith('CORP')) return 'CORP';
	return 'MIN';
}
// --- Constantes de API y elementos del DOM ---
const API_COTIZACIONES = '/monedas/cotizaciones_json/';
const API_TASAS_COMISIONES = '/monedas/tasas_comisiones/';
// Selects de monedas y campos del formulario
const selectOrigen = document.getElementById('moneda-origen');
const selectDestino = document.getElementById('moneda-destino');
const montoInput = document.getElementById('monto');
// Permite solo números enteros en el input de monto
montoInput.addEventListener('input', function(e) {
	let val = this.value.replace(/[^0-9]/g, '');
	this.value = val;
});
const resultadoDiv = document.getElementById('resultado-simulador');
const errorDiv = document.getElementById('error-simulador');
const form = document.getElementById('simulador-form');
const swapBtn = document.getElementById('swap-monedas');
// Variables para almacenar cotizaciones y tasas de comisiones
let cotizaciones = [];
let tasasComisiones = {};
// --- Funciones utilitarias para mostrar mensajes ---
function mostrarError(msg) {
	errorDiv.textContent = msg;
	errorDiv.classList.remove('d-none');
	resultadoDiv.classList.add('d-none');
}
// Muestra el resultado de la simulación
function mostrarResultado(msg) {
	resultadoDiv.innerHTML = msg;
	resultadoDiv.classList.remove('d-none');
	errorDiv.classList.add('d-none');
}
// Limpia los mensajes de error y resultado
function limpiarMensajes() {
	errorDiv.classList.add('d-none');
	resultadoDiv.classList.add('d-none');
}
// --- Carga las cotizaciones de monedas y llena los selects ---
async function cargarCotizaciones() {
	try {
		const resp = await fetch(API_COTIZACIONES);
		if (!resp.ok) throw new Error('No se pudo obtener cotizaciones');
		const data = await resp.json();
		cotizaciones = data.cotizaciones || [];
		// Extrae monedas únicas y agrega la base PYG
		const monedas = { 'PYG': true };
		cotizaciones.forEach(c => {
			if (c.moneda && !monedas[c.moneda]) {
				monedas[c.moneda] = true;
			}
		});
		// Llena los selects de origen y destino
		selectOrigen.innerHTML = '';
		selectDestino.innerHTML = '';
		Object.keys(monedas).forEach(codigo => {
			const opt1 = document.createElement('option');
			opt1.value = codigo;
			opt1.textContent = codigo;
			selectOrigen.appendChild(opt1);
			const opt2 = document.createElement('option');
			opt2.value = codigo;
			opt2.textContent = codigo;
			selectDestino.appendChild(opt2);
		});
		// Selección por defecto: PYG a USD
		let idxPYG = Array.from(selectOrigen.options).findIndex(opt => opt.value === 'PYG');
		let idxUSD = Array.from(selectDestino.options).findIndex(opt => opt.value === 'USD');
		if (idxPYG >= 0) selectOrigen.selectedIndex = idxPYG;
		if (idxUSD >= 0) selectDestino.selectedIndex = idxUSD;
	} catch (e) {
		mostrarError('Error al cargar cotizaciones: ' + e.message);
	}
}
// Carga las tasas de comisión desde la API
async function cargarTasasComisiones() {
	try {
		const resp = await fetch(API_TASAS_COMISIONES);
		if (!resp.ok) throw new Error('No se pudo obtener tasas de comisión');
		const data = await resp.json();
		tasasComisiones = data.tasas || {};
	} catch (e) {
		mostrarError('Error al cargar tasas de comisión: ' + e.message);
	}
}
// --- Simula la conversión de monedas según el segmento y descuento ---
async function simularConversion(monto, origen, destino) {
	if (origen === destino) {
		mostrarResultado(`El monto convertido es igual: ${monto}`);
		return;
	}

	// Obtiene el segmento de cliente activo
	const segmento = obtenerSegmentoClienteActivo();
	// Obtiene el descuento por segmento
	let descuento = 0;
	if (tasasComisiones && tasasComisiones[segmento.toLowerCase()]) {
		descuento = parseFloat(tasasComisiones[segmento.toLowerCase()].tasa_descuento) || 0;
	}
	// Texto para mostrar el tipo de cliente y descuento
	const infoCliente = `Tipo de cliente: ${segmento}`;
	const infoDescuento = `Descuento aplicado: ${descuento}%`;
	const salto = '<br>';

	// Obtener cotizaciones desde la vista de exchange
	let exchangeRates = [];
	try {
		const resp = await fetch('/exchange/rates/');
		if (!resp.ok) throw new Error('No se pudo obtener cotizaciones de exchange');
		const data = await resp.json();
		exchangeRates = data.rates || [];
	} catch (e) {
		mostrarError('Error al obtener cotizaciones de exchange: ' + e.message);
		return;
	}

	// Si convierto de PYG a moneda extranjera (VENTA)
	if (origen === 'PYG') {
		const tasa = exchangeRates.find(c => c.currency === destino);
		if (!tasa) {
			mostrarError('No se encontró cotización para la moneda de destino en exchange.');
			return;
		}
		const com = comisiones.find(c => c.currency === destino);
		const pb = (parseFloat(tasa.sell) + parseFloat(tasa.buy)) / 2;
		const comision_vta = com ? parseFloat(com.commission_sell) : 0;
		let tc_venta = parseFloat(tasa.sell);
		tc_venta = (pb + comision_vta - (comision_vta * descuento / 100));
		const montoConvertido = parseFloat(monto) / tc_venta;
		mostrarResultado(`${infoCliente}${salto}${infoDescuento}${salto}Monto convertido: ${montoConvertido.toFixed(2)} ${destino} (TC venta: ${tc_venta.toFixed(2)})`);
		return;
	}

	// Si convierto de moneda extranjera a PYG (COMPRA)
	if (destino === 'PYG') {
		const tasa = exchangeRates.find(c => c.currency === origen);
		if (!tasa) {
			mostrarError('No se encontró cotización para la moneda de origen en exchange.');
			return;
		}
		const com = comisiones.find(c => c.currency === origen);
		const pb = (parseFloat(tasa.sell) + parseFloat(tasa.buy)) / 2;
		const comision_com = com ? parseFloat(com.commission_buy) : 0;
		let tc_compra = parseFloat(tasa.buy) + comision_com;
		tc_compra = (pb - (comision_com - (comision_com * descuento / 100)));
		const montoConvertido = parseFloat(monto) * tc_compra;
		mostrarResultado(`${infoCliente}${salto}${infoDescuento}${salto}Monto convertido: ${montoConvertido.toFixed(2)} PYG (TC compra: ${tc_compra.toFixed(2)})`);
		return;
	}

	mostrarError('Solo se soportan conversiones directas con la moneda base (PYG).');
}
// --- Intercambia las monedas seleccionadas en los selects ---
swapBtn.addEventListener('click', function() {
	const tmp = selectOrigen.value;
	selectOrigen.value = selectDestino.value;
	selectDestino.value = tmp;
});
// --- Maneja el envío del formulario de simulación ---
form.addEventListener('submit', function(e) {
	e.preventDefault();
	limpiarMensajes();
	let monto = montoInput.value;
	if (!/^\d+$/.test(monto)) {
		mostrarError('Ingrese solo números enteros.');
		return;
	}
	monto = parseInt(monto, 10);
	const origen = selectOrigen.value;
	const destino = selectDestino.value;
	if (!monto || isNaN(monto) || monto <= 0) {
		mostrarError('Ingrese un monto válido.');
		return;
	}
	if (!origen || !destino) {
		mostrarError('Seleccione ambas monedas.');
		return;
	}
	simularConversion(monto, origen, destino);
});
// --- Inicialización: carga datos al cargar la página ---
window.addEventListener('DOMContentLoaded', async function() {
	await cargarCotizaciones();
	await cargarTasasComisiones();
	await cargarComisiones();
});
