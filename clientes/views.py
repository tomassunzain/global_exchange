from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Cliente
from .forms import AsignarUsuariosAClienteForm, ClienteForm

@login_required
def clientes_list(request):
    clientes = Cliente.objects.all().order_by("-id")
    return render(request, "clientes/clientes_list.html", {"clientes": clientes})

@login_required
def cliente_create(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente creado exitosamente.")
            return redirect("clientes:clientes_list")
    else:
        form = ClienteForm()
    return render(request, "clientes/cliente_form.html", {"form": form})

@login_required
def cliente_edit(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    if request.method == "POST":
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente actualizado.")
            return redirect("clientes:clientes_list")
    else:
        form = ClienteForm(instance=cliente)
    return render(request, "clientes/cliente_form.html", {"form": form, "cliente": cliente})

@login_required
def cliente_delete(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    if request.method == "POST":
        cliente.delete()
        messages.success(request, "Cliente eliminado.")
        return redirect("clientes:clientes_list")
    return render(request, "clientes/cliente_delete_confirm.html", {"cliente": cliente})

@login_required
def seleccionar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id, usuarios=request.user)
    request.session["cliente_activo"] = cliente.id
    messages.success(request, f"Ahora estás operando como cliente: {cliente.nombre}")
    return redirect("dashboard")

@login_required
def asignar_usuarios_a_cliente(request, cliente_id):
    cliente= get_object_or_404(Cliente, pk=cliente_id)
    if request.method == "POST":
        form = AsignarUsuariosAClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, f"Usuarios asignados al cliente: {cliente.nombre}.")
            return redirect("clientes:clientes_list")
    else:
        form = AsignarUsuariosAClienteForm(instance=cliente)
    return render(request, "clientes/asignar_usuarios_a_cliente.html", {"form": form, "cliente": cliente})
