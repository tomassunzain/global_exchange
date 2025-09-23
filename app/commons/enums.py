"""
Definición de enumeraciones utilizadas en la aplicación.
"""
from enum import Enum



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
