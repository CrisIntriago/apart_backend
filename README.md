# Proyecto APART

Este proyecto es una API REST construida con **Django** y **Django REST Framework (DRF)**. Utiliza **PostgreSQL** como base de datos y **UV** como gestor de entorno y dependencias.

## Requisitos

Antes de iniciar, asegúrate de tener instalado:

* [Python 3.12](https://www.python.org/downloads/)
* [UV](https://github.com/astral-sh/uv) (gestor de entorno y ejecución)
* PostgreSQL (versión 13+ recomendada)

> Para instalar `uv`, puedes usar:
>
> ```bash
> pip install uv
> ```

## 🧪 Instalación y ejecución del proyecto

### 1. Clonar el repositorio

```bash
git clone <URL_DE_TU_REPOSITORIO>
cd services/academy
```

### 2. Crear entorno virtual e instalar dependencias

```bash
uv sync
```

> Esto instalará automáticamente las dependencias listadas en `pyproject.toml`.

Claro, aquí tienes una sección lista para agregar al README, enfocada en **cómo generar el `SECRET_KEY`** de Django:

---


### 3. Configurar entorno

Asegúrate de tener una base de datos PostgreSQL activa. Crea una base de datos y actualiza tus variables en el archivo `.env`.

Ejemplo de configuración:

```env
SECRET_KEY=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
```

## Generar SECRET KEY para Django

Django requiere una clave secreta (`SECRET_KEY`) para funciones criptográficas internas como la firma de cookies o tokens. Puedes generar una clave segura con el siguiente comando:

```bash
uv run python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copia el valor generado y pégalo en tu archivo `.env`:

```env
SECRET_KEY=coloca_aquí_tu_clave_generada
```

### 4. Configurar archivo `.env`

Crea el archivo modifica según tus necesidades:

> El archivo `.env` contiene configuraciones necesarias como claves secretas, modo de entorno y credenciales de base de datos.

### 5. Aplicar migraciones y cargar datos iniciales

```bash
uv run manage.py makemigrations
uv run manage.py migrate
uv run manage.py createsuperuser
```

### 6. Levantar el servidor de desarrollo

```bash
uv run manage.py runserver
```

## ▶️ Comandos útiles con UV

Todos los comandos de Django deben ser ejecutados usando `uv run`, por ejemplo:

```bash
uv run manage.py makemigrations
uv run manage.py shell
```
Aquí tienes la sección actualizada para agregar al README, con los pasos adecuados para instalar una nueva librería usando `uv` de forma correcta y más segura (sin `pip install` directo):

---

## 📦 Agregar nuevas dependencias

Para agregar una nueva dependencia al proyecto, utiliza el comando `uv add`. Este comando actualiza automáticamente tu archivo `pyproject.toml` y sincroniza el entorno virtual.

### Ejemplo

Para instalar `drf-yasg`, ejecuta:

```bash
uv add drf-yasg
```

Esto:

* Instala la librería en el entorno virtual.
* Agrega automáticamente la dependencia en `pyproject.toml`.
* Mantiene sincronizada tu lista de paquetes.

> **Nota:** No uses `pip install` directamente, ya que no actualizará correctamente `pyproject.toml`.

Luego puedes continuar con los comandos de Django normalmente:

```bash
uv run manage.py migrate
uv run manage.py runserver
```

---

## 🧪 Ejecutar tests

Para correr los tests del proyecto, utiliza:

```bash
uv run manage.py test
```

Puedes correr un test específico con:

```bash
uv run manage.py test app.tests.test_nombre.TestClase.test_metodo
```

## 📦 Agregar nuevas dependencias

Para instalar nuevas dependencias (por ejemplo, `django-cors-headers`), ejecuta:

```bash
uv pip install django-cors-headers
uv pip compile pyproject.toml
```

Esto actualizará tu entorno virtual y las entradas correspondientes en `pyproject.toml`.