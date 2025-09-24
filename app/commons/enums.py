
from enum import Enum
"""
Definición de enumeraciones utilizadas en la aplicación.
"""

class TipoMedioAcreditacionEnum(Enum):
	CUENTA_BANCARIA = "cuenta_bancaria"
	BILLETERA = "billetera"


class EstadoRegistroEnum(Enum):
	ACTIVO = "activo"
	ELIMINADO = "eliminado"
	SUSPENDIDO = "suspendido"
