# global_exchange

Sistema de intercambio de divisas con gestión de usuarios y asignación de clientes.  
Desarrollado con Python, Django y PostgreSQL.

## Descripción

Este proyecto permite:

- Registro y gestión de usuarios.
- Asignación de clientes a usuarios.
- Gestión de sesiones y roles.
- Interfaz web funcional para administración y operaciones.

## Tecnologías

- Python 3.12+
- Django 5.2.5
- PostgreSQL 17.6
- psycopg2-binary 2.9.10

## Instalación

1. Clonar el repositorio:
    ```bash
    git clone https://github.com/tomassunzain/global_exchange.git
    cd global_exchange
2. Crear y activar un entorno virtual:
    ```bash
   python -m venv venv
   source venv/bin/activate       # Linux/macOS
   venv\Scripts\activate          # Windows
3. Instalar dependencias:
    ```bash
   pip install -r requirements.txt
4. Configurar la base de datos en `settings.py`:

   Editar el archivo `global_exchange/settings.py` con tus credenciales locales de PostgreSQL
    ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'db_globalex',
           'USER': 'postgres',
           'PASSWORD': 'masterkey',  # tu contraseña real
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
5. Aplicar migraciones:
    ```bash
   python manage.py migrate
6. Ejecutar el servidor
    ```bash
   python manage.py runserver
