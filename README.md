# Apart-backend


## Uso de venv en Python y gestión de dependencias con requirements.txt

### 1. Crear un entorno virtual con venv

Para crear un entorno virtual en Python, sigue estos pasos:

1. **Abre la terminal o línea de comandos**.
2. Navega hasta el directorio donde deseas crear el entorno virtual.
3. Ejecuta el siguiente comando para crear el entorno virtual:

    ```bash
    python3 -m venv nombre_del_entorno
    ```

    Sustituye `nombre_del_entorno` por el nombre que quieras darle a tu entorno virtual. Esto creará una carpeta con el nombre especificado, la cual contendrá el entorno virtual.

### 2. Activar el entorno virtual

Una vez que se haya creado el entorno virtual, debes activarlo:

- **En Windows**:

    ```bash
    .\nombre_del_entorno\Scripts\activate
    ```

- **En macOS o Linux**:

    ```bash
    source nombre_del_entorno/bin/activate
    ```

Cuando el entorno virtual está activado, verás el nombre del entorno en la terminal, lo que indica que estás trabajando dentro de él.

### 3. Instalar dependencias desde requirements.txt

Si tienes un archivo `requirements.txt` que contiene todas las dependencias necesarias para tu proyecto, puedes instalar estas dependencias de la siguiente manera:

1. **Asegúrate de que el entorno virtual esté activado**.
2. Ejecuta el siguiente comando para instalar las dependencias:

    ```bash
    pip install -r requirements.txt
    ```

Este comando leerá el archivo `requirements.txt` y descargará e instalará todas las dependencias que figuran en el archivo.

### 4. Iniciar la aplicación con Uvicorn

Para iniciar la aplicación, primero debes asegurarte de estar en el directorio adecuado donde se encuentra la aplicación. Supongamos que tu aplicación está en la carpeta `app`.

1. Asegúrate de que el entorno virtual esté activado.
2. Navega al directorio `./app/`:
   
   ```bash
   cd ./app/
3. Ejecuta la aplicación con uvicorn
    ```bash
    uvicorn nombre_de_tu_app:app --reload
### 5. Desactivar el entorno virtual

Cuando hayas terminado de trabajar, puedes desactivar el entorno virtual con el siguiente comando:

```bash
deactivate