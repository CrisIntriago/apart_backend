import os
from dotenv import load_dotenv
from pathlib import Path

# Obtén la ruta absoluta del directorio del script actual.
current_dir = Path(__file__).resolve().parent

# Remontando dos niveles por encima del directorio actual para llegar al archivo .env
env_path = current_dir.parent.parent / '.env'

load_dotenv(dotenv_path=env_path)
print(os.getenv('POSTGRES_DB'))

class Settings:
        PROJECT_NAME='projectname'
        PROJECT_VERSION='v1'
        POSTGRES_DB=os.getenv('POSTGRES_DB')
        POSTGRES_USER=os.getenv('POSTGRES_USER')
        POSTGRES_PASSWORD=os.getenv('POSTGRES_PASSWORD')
        POSTGRES_SERVER=os.getenv('POSTGRES_SERVER')
        POSTGRES_PORT=os.getenv('POSTGRES_PORT')
        #POSTGRES_URL=f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
        POSTGRES_URL=f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
        

settings = Settings()