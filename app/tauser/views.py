
from django.shortcuts import render
from .utils import obtener_datos_transaccion

from transaccion.models import Transaccion

def tramitar_transacciones(request):
    """
    Vista para tramitar transacciones de un cliente activo.
    Permite consultar datos de una transacción por ID y muestra mensajes de error si corresponde.
    """
    datos_transaccion = None
    error = None
    transaccion_id = ''
    cliente_activo_id = request.session.get('cliente_activo')
    transacciones_cliente = []
    if cliente_activo_id:
        transacciones_cliente = Transaccion.objects.filter(cliente_id=cliente_activo_id).order_by('-fecha')
    if request.method == 'POST':
        transaccion_id = request.POST.get('transaccion_id', '').strip()
        if transaccion_id:
            # Solo permitir IDs de transacciones del cliente activo
            if not transacciones_cliente.filter(pk=transaccion_id).exists():
                error = 'La transacción no pertenece al cliente seleccionado.'
            else:
                try:
                    datos_transaccion = obtener_datos_transaccion(transaccion_id)
                    if datos_transaccion is None:
                        error = 'No se encontró la transacción.'
                except Exception as e:
                    error = str(e)
        else:
            error = 'Debe ingresar un ID de transacción.'
    return render(request, 'tauser/tramitar_transacciones.html', {
        'datos_transaccion': datos_transaccion,
        'error': error,
        'transaccion_id': transaccion_id,
        'transacciones_cliente': transacciones_cliente,
    })


def nuevo_tauser(request):
    """
    Renderiza la página para crear un nuevo TAUser.
    """
    return render(request, 'tauser/nuevo_tauser.html')


def lista_tausers(request):
    """
    Renderiza la página con el listado de TAUsers.
    """
    return render(request, 'tauser/lista_tausers.html')
