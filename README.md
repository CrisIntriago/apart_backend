# Proyecto API REST con Django y UV

Este proyecto es una API REST construida con **Django** y **Django REST Framework** (DRF). Para gestionar las dependencias y ejecutar el proyecto, utilizaremos **UV**, un administrador de paquetes para Python que facilita la instalación y la ejecución del proyecto.

## Requisitos

Antes de iniciar el proyecto, asegúrate de tener los siguientes requisitos:


- **Python 3.12**
- **UV** (para gestionar el entorno y ejecutar el servidor)

## Paso 1: Cl   onar el repositorio

Primero, necesita clonar este repositorio en su entorno local. Puede hacer esto con el siguiente comando:

```sh
git clone https://gitlab.com/kamina-development/kamina-backend.git
```

## Paso 2: Navegar a la carpeta raíz del proyecto

Una vez clonado el repositorio, navegue a la carpeta raíz del proyecto:

```sh
cd services/academy
```

## Paso 3: Crear el entorno virtual con sus dependencias

Necesitamos cargar el entorno virtual, para esto utilizamos uv:

```bash
uv sync
```

## Ejecutar comando de Django

En vez usar: 
```sh
python manage.py startapp
```

Usaremos:
```sh
uv run manage.py startapp
```

# Configurar variables de ambiente

Las variables de entorno se cargan desde el archivo pyproject.toml y se puede agregar los archivos mediante envfile, aqui un ejemplo de task con su variable de entorno:
[tool.poe.tasks]
dev.cmd = "uvicorn app.main:app --reload"
dev.envfile = ".env.dev"

## Paso 1: Copiar archivo .env
Cada uno de los proyectos debe tener un archivo .env.example el mismo que indica los nombres de las variables necesarias para poder ser ejecutado, este archivo debe ser copiado y renombrado con el nombre `.env` y se deben reemplazar los valores por los deseados.