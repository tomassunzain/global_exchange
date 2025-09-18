// Simulador de Conversiones dinámico 
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('simulador-form');
    const selectOrigen = document.getElementById('moneda-origen');
    const selectDestino = document.getElementById('moneda-destino');
    const inputMonto = document.getElementById('monto');
    let ratesMap = {};

    // Detect endpoint según contexto (dashboard usa /exchange/rates/, landing puede usar ?source=local)
    let endpoint = '/exchange/rates/';
    if (form && form.hasAttribute('data-source')) {
        endpoint += '?source=' + form.getAttribute('data-source');
    }

    fetch(endpoint)
        .then(res => res.json())
        .then(data => {
            if (data.rates) {
                // Obtener todas las monedas únicas
                const monedas = Array.from(new Set(data.rates.flatMap(rate => [rate.currency, rate.base_currency].filter(Boolean))));
                // Poblar selects una sola vez
                monedas.forEach(moneda => {
                    const opt1 = document.createElement('option');
                    opt1.value = moneda;
                    opt1.textContent = moneda;
                    selectOrigen.appendChild(opt1);
                    const opt2 = document.createElement('option');
                    opt2.value = moneda;
                    opt2.textContent = moneda;
                    selectDestino.appendChild(opt2);
                });
                // Seleccionar por defecto PYG y USD
                selectOrigen.value = 'PYG';
                selectDestino.value = 'USD';
                // Mapear tasas para acceso rápido
                data.rates.forEach(rate => {
                    ratesMap[`${rate.currency}_${rate.base_currency}`] = {
                        buy: parseFloat(rate.buy),
                        sell: parseFloat(rate.sell)
                    };
                });
            }
        });

    // Formatear el input de monto con puntos de miles para cualquier moneda
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
        // Solo permitir números, punto y coma en la entrada
        inputMonto.addEventListener('input', function(e) {
            // Permitir solo dígitos, puntos, comas y borrar lo demás
            let clean = this.value.replace(/[^\d.,]/g, '');
            if (this.value !== clean) {
                this.value = clean;
            }
            formatMontoInput();
        });
    }

    function formatNumberCustom(num) {
        if (typeof num !== 'number') return num;
        return num.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    if (form) {
        const errorDiv = document.getElementById('error-simulador');
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            errorDiv.classList.add('d-none');
            errorDiv.innerHTML = '';
            // Quitar puntos y cambiar coma por punto para parsear
            let rawMonto = inputMonto.value.replace(/\./g, '').replace(/,/g, '.');
            // Validar que sea un número positivo válido
            if (!/^\d+(\.\d{1,2})?$/.test(rawMonto) || isNaN(parseFloat(rawMonto)) || parseFloat(rawMonto) <= 0) {
                errorDiv.classList.remove('d-none');
                errorDiv.innerHTML = 'Ingrese un monto válido (solo números, sin letras ni símbolos).';
                return;
            }
            const monto = parseFloat(rawMonto);
            const origen = selectOrigen.value;
            const destino = selectDestino.value;
            let resultado = null;

            if (origen === destino) {
                const resultadoDiv = document.getElementById('resultado-simulador');
                resultadoDiv.classList.remove('d-none', 'alert-success');
                resultadoDiv.classList.add('alert-danger');
                resultadoDiv.innerHTML = 'La moneda de origen no puede ser igual que la moneda de destino.';
                return;
            } else if (origen === 'PYG') {
                // PYG a internacional: usar tasa sell de destino
                let rate = ratesMap[`${destino}_PYG`];
                resultado = rate ? monto / rate.sell : null;
            } else if (destino === 'PYG') {
                // Internacional a PYG: usar tasa buy de origen
                let rate = ratesMap[`${origen}_PYG`];
                resultado = rate ? monto * rate.buy : null;
            } else {
                // Internacional a internacional: SIEMPRE pasar por PYG
                let rateOrigen = ratesMap[`${origen}_PYG`];
                let rateDestino = ratesMap[`${destino}_PYG`];
                if (rateOrigen && rateDestino) {
                    let montoEnPYG = monto * rateOrigen.buy;
                    resultado = montoEnPYG / rateDestino.sell;
                } else {
                    resultado = null;
                }
            }

            const resultadoDiv = document.getElementById('resultado-simulador');
            if (resultado !== null && !isNaN(resultado)) {
                resultadoDiv.classList.remove('d-none', 'alert-danger');
                resultadoDiv.classList.add('alert-success');
                resultadoDiv.innerHTML = `<strong>Resultado:</strong> ${inputMonto.value} ${origen} = ${formatNumberCustom(resultado)} ${destino}`;
            } else {
                resultadoDiv.classList.remove('d-none', 'alert-success');
                resultadoDiv.classList.add('alert-danger');
                resultadoDiv.innerHTML = 'Conversión no válida.';
            }
        });

        // Botón para alternar monedas
        const swapBtn = document.getElementById('swap-monedas');
        if (swapBtn) {
            swapBtn.addEventListener('click', function() {
                const temp = selectOrigen.value;
                selectOrigen.value = selectDestino.value;
                selectDestino.value = temp;
            });
        }
    }
});
