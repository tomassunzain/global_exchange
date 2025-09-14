
from django.db import models
from clientes.models import Cliente


class PaymentMethod(models.Model):
	"""
	Modelo que representa un método de pago disponible en el sistema.

	:ivar cliente: Cliente al que pertenece el método de pago.
	:vartype cliente: Cliente
	:ivar name: Nombre del método de pago.
	:vartype name: str
	:ivar description: Descripción opcional del método de pago.
	:vartype description: str
	:ivar created_at: Fecha de creación.
	:vartype created_at: datetime
	:ivar updated_at: Fecha de última actualización.
	:vartype updated_at: datetime
	"""
	cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="metodos_pago", verbose_name="Cliente")
	name = models.CharField(max_length=100, verbose_name="Nombre")
	description = models.TextField(blank=True, verbose_name="Descripción")
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = "Método de Pago"
		verbose_name_plural = "Métodos de Pago"
		ordering = ["name"]

	def __str__(self):
		"""
		Retorna el nombre del método de pago.

		:return: Nombre del método de pago.
		:rtype: str
		"""
		return self.name
