from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.queries.user_queries import UserQueries
from app.dependencies.dependencies import get_db

router = APIRouter(tags=['User'])

header_scheme = APIKeyHeader(name="x-key")

@router.get('/verify-db-connection')
async def verify_connection(db: AsyncSession = Depends(get_db)):
    user_queries = UserQueries(session=db)
    try:
        await user_queries.get_first_user()
    except Exception as e:
        if "[Errno 61] Connect call failed" in str(e):
            print("Verifica la dirección y el puerto, y asegúrate de que el servidor PostgreSQL esté en ejecución.")
        else:
            print(f'Error en conexión 222: {str(e)}')
        return JSONResponse(
            status_code=500,
            content={"message": 'Error en conexión'},
        )
    else:
        return JSONResponse(
            status_code=200,
            content={"message": 'Conexión exitosa'},
        )