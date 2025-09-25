// Script principal del simulador de conversiones
document.addEventListener('DOMContentLoaded', function() {
    // Variables globales para cotizaciones y comisiones
    let comision_venta = null;
    let comision_compra = null;
    let cotizacionesSistema = [];
    let moneda_cotizada_venta = null;
    let moneda_cotizada_compra = null;
    let moneda_base_venta = null;
    let moneda_base_compra = null;

    // Obtener cotizaciones del sistema desde la API
    fetch('/monedas/cotizaciones_json/')
        .then(res => res.json())
        .then(data => {
            if (data.cotizaciones) {
                cotizacionesSistema = data.cotizaciones;
                actualizarValoresMonedaBase();
            }
        })
        .catch(err => { if (window.DEBUG) console.error('Error cotizaciones:', err); });
    // Manejo del cliente activo seleccionado en el dashboard
    let clienteActivoId = null;
    let clienteActivoTipo = null;
    const selectCliente = document.querySelector('select[name="cliente_id"]');
    function obtenerTipoCliente(option) {
        let tipoMatch = option.textContent.match(/\(([^)]+)\)/);
        return tipoMatch ? tipoMatch[1].toLowerCase() : null;
    }
    function actualizarClienteActivo(select) {
        clienteActivoId = select.value;
        let selectedOption = select.options[select.selectedIndex];
        clienteActivoTipo = obtenerTipoCliente(selectedOption);
    }
    if (selectCliente) {
        actualizarClienteActivo(selectCliente);
        if (window.DEBUG) console.log('Cliente activo inicial:', clienteActivoId, clienteActivoTipo);
        selectCliente.addEventListener('change', function() {
            actualizarClienteActivo(this);
            const form = document.getElementById('simulador-form');
            let loadingDiv = document.createElement('div');
            loadingDiv.id = 'simulador-loading';
            loadingDiv.className = 'alert alert-info';
            loadingDiv.innerHTML = 'Cargando datos del simulador...';
            if (form) {
                form.parentNode.insertBefore(loadingDiv, form);
                Array.from(form.elements).forEach(el => el.disabled = true);
            }
        });
    }
    // Obtener tasas de descuento por tipo de cliente desde la API
    let tasasDescuento = {};
    fetch('/monedas/tasas_comisiones/')
        .then(res => res.json())
        .then(data => {
            if (data.tasas) {
                tasasDescuento = data.tasas;
            }
        })
        .catch(err => { if (window.DEBUG) console.error('Error tasas comisiones:', err); });

    // Elementos principales del formulario y mapa de tasas
    const form = document.getElementById('simulador-form');
    const selectOrigen = document.getElementById('moneda-origen');
    const selectDestino = document.getElementById('moneda-destino');
    const inputMonto = document.getElementById('monto');
    let ratesMap = {};

    // Determinar endpoint de cotizaciones según contexto
    let endpoint = '/exchange/rates/';
    if (form && form.hasAttribute('data-source')) {
        endpoint += '?source=' + form.getAttribute('data-source');
    }

    // Actualiza las variables de tasas y comisiones según la selección de monedas
    function actualizarValoresMonedaBase() {
        const origen = selectOrigen.value;
        const destino = selectDestino.value;
        moneda_cotizada_compra = null;
        moneda_cotizada_venta = null;
        moneda_base_compra = null;
        moneda_base_venta = null;
        comision_venta = null;
        comision_compra = null;
        if (cotizacionesSistema.length > 0 && origen && destino && origen !== destino) {
            if (origen === 'PYG') {
                let cotizacionVenta = cotizacionesSistema.find(c => c.moneda === destino && c.base === 'PYG');
                moneda_cotizada_venta = cotizacionVenta ? parseFloat(cotizacionVenta.venta) : null;
                let rate = ratesMap[`${destino}_PYG`];
                moneda_base_venta = rate ? rate.sell : null;
            } else if (destino === 'PYG') {
                let cotizacionCompra = cotizacionesSistema.find(c => c.moneda === origen && c.base === 'PYG');
                moneda_cotizada_compra = cotizacionCompra ? parseFloat(cotizacionCompra.compra) : null;
                let rate = ratesMap[`${origen}_PYG`];
                moneda_base_compra = rate ? rate.buy : null;
            } else {
                let cotizacionCompra = cotizacionesSistema.find(c => c.moneda === origen && c.base === 'PYG');
                let cotizacionVenta = cotizacionesSistema.find(c => c.moneda === destino && c.base === 'PYG');
                moneda_cotizada_compra = cotizacionCompra ? parseFloat(cotizacionCompra.compra) : null;
                moneda_cotizada_venta = cotizacionVenta ? parseFloat(cotizacionVenta.venta) : null;
                let rateOrigen = ratesMap[`${origen}_PYG`];
                let rateDestino = ratesMap[`${destino}_PYG`];
                moneda_base_compra = rateOrigen ? rateOrigen.buy : null;
                moneda_base_venta = rateDestino ? rateDestino.sell : null;
            }
        }
        if (moneda_base_venta !== null && moneda_cotizada_venta !== null) {
            comision_venta = Math.abs(moneda_base_venta - moneda_cotizada_venta);
        }
        if (moneda_base_compra !== null && moneda_cotizada_compra !== null) {
            comision_compra = Math.abs(moneda_base_compra - moneda_cotizada_compra);
        }
        if (window.DEBUG) {
            console.log('moneda_base_compra:', moneda_base_compra);
            console.log('moneda_base_venta:', moneda_base_venta);
            console.log('moneda_cotizada_compra:', moneda_cotizada_compra);
            console.log('moneda_cotizada_venta:', moneda_cotizada_venta);
            console.log('comision_venta:', comision_venta);
            console.log('comision_compra:', comision_compra);
        }
        const cards = document.querySelectorAll('.card');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            setTimeout(() => {
                card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });
    }

    // (Reloj en vivo y efecto visual de botones movidos a ui-helpers.js)

    // Obtener tasas de cambio y poblar selects de monedas
    fetch(endpoint)
        .then(res => res.json())
        .then(data => {
            if (data.rates) {
                const monedasSet = new Set();
                data.rates.forEach(rate => {
                    if (rate.currency) monedasSet.add(rate.currency);
                    if (rate.base_currency) monedasSet.add(rate.base_currency);
                });
                monedasSet.forEach(moneda => {
                    const opt1 = document.createElement('option');
                    opt1.value = moneda;
                    opt1.textContent = moneda;
                    selectOrigen.appendChild(opt1);
                    const opt2 = document.createElement('option');
                    opt2.value = moneda;
                    opt2.textContent = moneda;
                    selectDestino.appendChild(opt2);
                });
                selectOrigen.value = 'PYG';
                selectDestino.value = 'USD';
                data.rates.forEach(rate => {
                    ratesMap[`${rate.currency}_${rate.base_currency}`] = {
                        buy: parseFloat(rate.buy),
                        sell: parseFloat(rate.sell)
                    };
                });
                if (window.DEBUG) console.log('ratesMap keys:', Object.keys(ratesMap));
                actualizarValoresMonedaBase();
                selectOrigen.addEventListener('change', actualizarValoresMonedaBase);
                selectDestino.addEventListener('change', actualizarValoresMonedaBase);
            }
        })
        .catch(err => { if (window.DEBUG) console.error('Error rates:', err); });

    // Formatea el input de monto con separador de miles
    function formatMontoInput() {
        let value = inputMonto.value.replace(/\./g, '').replace(/,/g, '.');
        if (!value) return;
        let partes = value.split('.');
        let entero = partes[0];
        let decimal = partes[1] || '';
        entero = entero.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
        inputMonto.value = decimal ? entero + ',' + decimal : entero;
    }
    if (inputMonto) {
        inputMonto.addEventListener('input', function() {
            let clean = this.value.replace(/[^\d.,]/g, '');
            if (this.value !== clean) {
                this.value = clean;
            }
            formatMontoInput();
        });
    }

    // Formatea un número a string con dos decimales y separador de miles
    function formatNumberCustom(num) {
        if (typeof num !== 'number') return num;
        return num.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    // Lógica principal del simulador: validación, cálculo y presentación de resultados
    if (form) {
        const errorDiv = document.getElementById('error-simulador');
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            errorDiv.classList.add('d-none');
            errorDiv.innerHTML = '';
            actualizarValoresMonedaBase();
            let rawMonto = inputMonto.value.replace(/\./g, '').replace(/,/g, '.');
            if (!/^\d+(\.\d{1,2})?$/.test(rawMonto) || isNaN(parseFloat(rawMonto)) || parseFloat(rawMonto) <= 0) {
                errorDiv.classList.remove('d-none');
                errorDiv.innerHTML = 'Ingrese un monto válido (solo números, sin letras ni símbolos).';
                return;
            }
            const monto = parseFloat(rawMonto);
            const origen = selectOrigen.value;
            const destino = selectDestino.value;
            let resultado = null;
            const debugVars = {
                moneda_base_venta,
                moneda_base_compra,
                moneda_cotizada_venta,
                moneda_cotizada_compra,
                comision_venta,
                comision_compra,
                clienteActivoTipo,
                tasasDescuento,
                origen,
                destino
            };
            if (window.DEBUG) console.log('DEBUG VARS SUBMIT:', debugVars);
            const resultadoDiv = document.getElementById('resultado-simulador');
            if (origen === destino) {
                resultadoDiv.classList.remove('d-none', 'alert-success');
                resultadoDiv.classList.add('alert-danger');
                resultadoDiv.innerHTML = 'La moneda de origen no puede ser igual que la moneda de destino.';
                return;
            }
            let tasa_desc = 0;
            let tipoClienteKey = clienteActivoTipo;
            if (clienteActivoTipo === 'minorista') tipoClienteKey = 'min';
            if (clienteActivoTipo === 'corporativo') tipoClienteKey = 'corp';
            if (clienteActivoTipo === 'vip') tipoClienteKey = 'vip';
            if (tipoClienteKey && tasasDescuento[tipoClienteKey] !== undefined) {
                let t = tasasDescuento[tipoClienteKey];
                if (typeof t === 'object' && t.tasa_descuento !== undefined) {
                    tasa_desc = parseFloat(t.tasa_descuento);
                } else {
                    tasa_desc = parseFloat(t);
                }
            }
            if (origen === 'PYG') {
                if (moneda_base_venta !== null && comision_venta !== null) {
                    let divisor = moneda_base_venta + comision_venta - (comision_venta * tasa_desc / 100);
                    resultado = divisor !== 0 ? monto / divisor : null;
                } else {
                    resultado = null;
                }
            } else if (destino === 'PYG') {
                if (moneda_base_compra !== null && comision_compra !== null) {
                    let factor = moneda_base_compra + (comision_compra - (comision_compra * tasa_desc / 100));
                    resultado = monto * factor;
                } else {
                    resultado = null;
                }
            } else {
                if (moneda_base_compra !== null && comision_compra !== null && moneda_base_venta !== null && comision_venta !== null) {
                    let factor = moneda_base_compra - (comision_compra - (comision_compra * tasa_desc / 100));
                    let divisor = moneda_base_venta + comision_venta - (comision_venta * tasa_desc / 100);
                    let montoEnPYG = monto * factor;
                    resultado = divisor !== 0 ? montoEnPYG / divisor : null;
                } else {
                    resultado = null;
                }
            }
            if (resultado !== null && !isNaN(resultado)) {
                resultadoDiv.classList.remove('d-none', 'alert-danger');
                resultadoDiv.classList.add('alert-success');
                let detalle = '';
                let tipoClienteHtml = `<br><small>Tipo de cliente: <b>${clienteActivoTipo}</b><br>Tasa descuento detectada: <b>${tasa_desc}%</b></small>`;
                if (origen === 'PYG') {
                    let divisor = moneda_base_venta + comision_venta - (comision_venta * tasa_desc / 100);
                    detalle = `<br><small><b>Cotización aplicada:</b> ${divisor}</small>`;
                    /*
                    detalle += `<br><small>Fórmula: Resultado = Monto / [TasaBaseVenta + (ComisiónVenta - ComisiónVenta×Descuento/100)]<br>
                    Monto: ${monto}<br>
                    TasaBaseVenta: ${moneda_base_venta}<br>
                    ComisiónVenta: ${comision_venta}<br>
                    Descuento: ${tasa_desc}%<br>
                    Denominador: ${divisor}
                    </small>`;
                    */
                } else if (destino === 'PYG') {
                    let com_desc = comision_compra - (comision_compra * tasa_desc / 100);
                    let factor = moneda_base_compra + com_desc;
                    detalle = `<br><small><b>Cotización aplicada:</b> ${factor}</small>`;
                    /*
                    detalle += `<br><small>Fórmula: Resultado = Monto × [TasaBaseCompra + (ComisiónCompra - ComisiónCompra×Descuento/100)]<br>
                    Monto: ${monto}<br>
                    TasaBaseCompra: ${moneda_base_compra}<br>
                    ComisiónCompra: ${comision_compra}<br>
                    Descuento: ${tasa_desc}%<br>
                    Comisión con descuento: ${com_desc}<br>
                    Factor: ${factor}
                    </small>`;
                    */
                } else {
                    let com_desc = comision_compra - (comision_compra * tasa_desc / 100);
                    let factor = moneda_base_compra - com_desc;
                    let divisor = moneda_base_venta + comision_venta - (comision_venta * tasa_desc / 100);
                    //let montoEnPYG = monto * factor;
                    detalle = `<br><small><b>Cotización aplicada:</b> ${divisor}</small>`;
                    /*
                    detalle += `<br><small>Fórmula: Resultado = (Monto × [TasaBaseCompra - (ComisiónCompra - ComisiónCompra×Descuento/100)]) / [TasaBaseVenta + (ComisiónVenta - ComisiónVenta×Descuento/100)]<br>
                    Monto: ${monto}<br>
                    TasaBaseCompra: ${moneda_base_compra}<br>
                    ComisiónCompra: ${comision_compra}<br>
                    Descuento: ${tasa_desc}%<br>
                    Comisión con descuento: ${com_desc}<br>
                    Factor: ${factor}<br>
                    MontoEnPYG: ${montoEnPYG}<br>
                    TasaBaseVenta: ${moneda_base_venta}<br>
                    ComisiónVenta: ${comision_venta}<br>
                    Denominador: ${divisor}
                    </small>`;
                    */
                }
                resultadoDiv.innerHTML = `<strong>Resultado:</strong> ${inputMonto.value} ${origen} = ${formatNumberCustom(resultado)} ${destino} ${tipoClienteHtml} ${detalle}`;
            } else {
                let debugHtml = '<strong>Conversión no válida.</strong><br><pre style="font-size:12px">';
                for (const [k, v] of Object.entries(debugVars)) {
                    debugHtml += `${k}: ${JSON.stringify(v)}\n`;
                }
                debugHtml += '</pre>';
                resultadoDiv.classList.remove('d-none', 'alert-success');
                resultadoDiv.classList.add('alert-danger');
                resultadoDiv.innerHTML = debugHtml;
            }
        });
        // Botón para intercambiar las monedas de origen y destino en el simulador
        const swapBtn = document.getElementById('swap-monedas');
        if (swapBtn) {
            swapBtn.addEventListener('click', function() {
                const temp = selectOrigen.value;
                selectOrigen.value = selectDestino.value;
                selectDestino.value = temp;
                actualizarValoresMonedaBase();
            });
        }
    }
});