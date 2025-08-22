
from pathlib import Path
import os
import sys


root_doc = "index" #para definir el archivo raiz
source_suffix = {
    ".md": "markdown", #para indicarle que tipo de archivo es
}

# para irnos a la raiz del repo
# docs/source -> docs -> <raiz del repo>
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# sirve para indicarle a django la configuracion del proyecto, en donde esta
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "global_exchange.settings")
import django
django.setup()

project = "global_exchange"
author = "augusto"
language = "es"

extensions = [
    "myst_parser",            # permitir Markdown
    "sphinx.ext.autodoc",     # permite generar documentacion a partir de los docstrings del codigo
    "sphinx.ext.napoleon",    # docstrings estilo Google/NumPy
    "sphinx.ext.viewcode",    # enlaces al código fuente
    "sphinxcontrib.mermaid",  # permitir memaid
]






