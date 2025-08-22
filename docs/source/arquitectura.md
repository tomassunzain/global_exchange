# Arquitectura

```{mermaid}
flowchart LR
A[Navegador] --> B[Nginx]
B --> C[Django (Gunicorn)]
C --> D[(PostgreSQL)]
C --> E[(Redis)]
C --> F[(S3 Storage)]