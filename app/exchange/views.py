
import json
import os
import requests
from django.http import JsonResponse
from django.conf import settings
from django.views import View


class ExchangeRatesView(View):
    """
    Vista basada en clases que gestiona la obtención de tasas de cambio.

    Permite elegir la fuente de datos de las tasas:
    
    - ``?source=api`` → Consume una API externa definida en la configuración.
    - ``?source=local`` o sin parámetro → Usa un archivo JSON de prueba (mock).

    :raises JsonResponse: En caso de error en el consumo de API o lectura del archivo local.
    """

    def get(self, request):
        """
        Maneja las solicitudes GET para obtener las tasas de cambio.

        :param request: Objeto HttpRequest de Django.
        :type request: HttpRequest
        :queryparam str source: Fuente de datos (``api`` o ``local``). Por defecto, ``local``.
        :return: Respuesta JSON con las tasas de cambio o un error.
        :rtype: JsonResponse

        **Ejemplos de uso**:

        - ``GET /exchange/rates?source=api``  
          Devuelve las tasas obtenidas de la API externa.

        - ``GET /exchange/rates``  
          Devuelve las tasas desde el archivo local ``mock_exchange_rates.json``.
        """
        source = request.GET.get('source', 'local')

        if source == 'api':
            # --- CONSUMO DE API EXTERNA ---
            try:
                url = "http://localhost:9000/api/rates/latest"  # Cambia por la API real
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
            return JsonResponse({'rates': data})

        # --- MODO LOCAL: LEE EL MOCK JSON ---
        else:
            json_path = os.path.join(settings.BASE_DIR, 'exchange', 'mock_data', 'mock_exchange_rates.json')
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
            return JsonResponse({'rates': data})
