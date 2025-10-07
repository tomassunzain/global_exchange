# Límites de transacción por tipo de cliente
CLIENT_LIMITS = {
    'minorista': {
        'diario': 2000000,    # monto máximo diario
        'mensual': 10000000,  # monto máximo mensual
    },
    'corporativo': {
        'diario': 5000000,
        'mensual': 25000000,
    },
    'vip': {
        'diario': 10000000,
        'mensual': 50000000,
    },
}
