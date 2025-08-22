from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def role_required(*role_names):
    """
    Decorator for views that checks if the logged-in user
    has at least one of the required roles.
    Usage:
        @role_required("Admin")
        @role_required("Admin", "Manager")
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, "You must log in to access this page.")
                return redirect("usuarios:login")

            if not request.user.has_any_role(*role_names):
                messages.error(request, "You don’t have permission to access this page.")
                return redirect("home")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
