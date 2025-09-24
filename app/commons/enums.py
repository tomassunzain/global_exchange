
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

# Enum para tipos de pago
class PaymentTypeEnum(Enum):
	TARJETA = "tarjeta"
	CUENTA_BANCARIA = "cuenta_bancaria"
	BILLETERA = "billetera"
	CHEQUE = "cheque"
