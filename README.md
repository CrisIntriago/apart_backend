# Apart-backend


## Gestión de dependencias con requirements.txt


### 1. Instalar dependencias desde requirements.txt

Si tienes un archivo `requirements.txt` que contiene todas las dependencias necesarias para tu proyecto, puedes instalar estas dependencias de la siguiente manera:

Ejecuta el siguiente comando para instalar las dependencias:

    ```bash
    pip install -r requirements.txt
    ```

Este comando leerá el archivo `requirements.txt` y descargará e instalará todas las dependencias que figuran en el archivo.

### 2. Iniciar la aplicación con Uvicorn

Para iniciar la aplicación, primero debes asegurarte de estar en el directorio adecuado donde se encuentra la aplicación. Supongamos que tu aplicación está en la carpeta `app`.

1. Ejecuta la aplicación con uvicorn
    ```bash
    uvicorn nombre_de_tu_app:app --reload