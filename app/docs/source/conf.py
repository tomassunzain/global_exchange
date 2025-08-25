# docs/source/conf.py
from pathlib import Path
import os
import sys
import importlib
import django
from django.conf import settings
from datetime import datetime

# ── Proyecto ───────────────────────────────────────────────────────────────────
DJANGO_PROJECT_PACKAGE = "global_exchange"   # ← ajustá si tu paquete raíz cambia

# ── Documento raíz y sufijos ───────────────────────────────────────────────────
root_doc = "index"
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}

# ── Rutas del repo ─────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# ── Django setup ───────────────────────────────────────────────────────────────
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"{DJANGO_PROJECT_PACKAGE}.settings")
django.setup()

# ── Metadatos ──────────────────────────────────────────────────────────────────
project = DJANGO_PROJECT_PACKAGE
author = "Grupo 10"
language = "es"
copyright = f"{datetime.now().year}, {author}"

# ── Extensiones ────────────────────────────────────────────────────────────────
extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "autoapi.extension",
    "sphinxcontrib.mermaid",
]

# ── Tema/HTML ──────────────────────────────────────────────────────────────────
html_theme = "sphinx_rtd_theme"
templates_path = ["_templates"]
html_static_path = ["_static"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**/__pycache__/**"]

# ── MyST extra ─────────────────────────────────────────────────────────────────
myst_enable_extensions = ["linkify", "deflist", "tasklist"]

# ── Intersphinx (links a docs externas) ────────────────────────────────────────
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "django": ("https://docs.djangoproject.com/en/stable/", None),
}

# ── Autodoc / Autosummary ──────────────────────────────────────────────────────
autosummary_generate = True
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    # Activá estas si querés ver TODO-TODO (incluye privados/dunders):
    # "private-members": True,
    # "special-members": "__init__,__call__",
    # "inherited-members": True,
}

# ── Helpers ────────────────────────────────────────────────────────────────────
def _is_local_module(mod_path: str) -> bool:
    try:
        p = Path(mod_path).resolve()
        return str(p).startswith(str(ROOT)) and "site-packages" not in str(p)
    except Exception:
        return False

def _import_any_prefix(dotted: str):
    """
    Intenta importar `dotted` completo; si falla, corta el último segmento
    e intenta de nuevo hasta que algo importe (o devuelva None).
    p.ej.: "usuarios.apps.UsuariosConfig" -> "usuarios"
           "global_exchange.apps.usuarios" -> "global_exchange.apps" -> "global_exchange"
    """
    parts = dotted.split(".")
    while parts:
        name = ".".join(parts)
        try:
            return importlib.import_module(name)
        except Exception:
            parts.pop()
    return None

# ── AutoAPI: descubrir todas las apps y el paquete raíz ────────────────────────
autoapi_dirs_set = set()

# 1) paquete del proyecto
try:
    pkg = importlib.import_module(DJANGO_PROJECT_PACKAGE)
    if getattr(pkg, "__file__", None) and _is_local_module(pkg.__file__):
        autoapi_dirs_set.add(str(Path(pkg.__file__).resolve().parent))
except Exception:
    pass

# 2) todas las apps locales en INSTALLED_APPS (robusto frente a AppConfig strings)
for app in settings.INSTALLED_APPS:
    # ignorar libs externas comunes
    if app.startswith(("django.", "rest_framework", "drf_", "sphinx", "autoapi", "myst_parser")):
        continue
    mod = _import_any_prefix(app)
    if mod and getattr(mod, "__file__", None) and _is_local_module(mod.__file__):
        autoapi_dirs_set.add(str(Path(mod.__file__).resolve().parent))

autoapi_dirs = sorted(autoapi_dirs_set)

# 3) Fallback: si quedó vacío, apunta al paquete raíz del proyecto
if not autoapi_dirs:
    fallback = (ROOT / DJANGO_PROJECT_PACKAGE)
    if fallback.exists():
        autoapi_dirs = [str(fallback)]
    else:
        # último recurso: escanear todo el repo (menos venv/docs), no ideal pero garantiza salida
        autoapi_dirs = [str(ROOT)]
        # para evitar ruido, aseguramos ignore amplio abajo

# ── AutoAPI opciones (única definición, sin duplicados) ────────────────────────
autoapi_type = "python"
autoapi_add_toctree_entry = True
autoapi_keep_files = False
autoapi_options = [
    "members",
    "undoc-members",
    "private-members",     # ← incluye métodos/atributos que empiezan con "_"
    "special-members",     # ← incluye todos los métodos dunder (__init__, __str__, etc.)
    "show-inheritance",
    "show-module-summary",
    "imported-members",
]
autoapi_ignore = [
    "*/migrations/*",
    "*/tests/*",
    "*/__pycache__/*",
    "manage.py",
    "docs/*",
    "venv/*",
    ".venv/*",
]

# ── Log útil al build (para verificar qué directorios se escanean) ─────────────
print("[AutoAPI] Escaneando directorios:", *autoapi_dirs, sep="\n - ")
