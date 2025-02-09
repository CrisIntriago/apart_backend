from fastapi import FastAPI
from app.routes.user import router as user_router
from contextlib import asynccontextmanager
from app.dependencies.dependencies import get_db
from fastapi.security import HTTPBearer
from app.core.config import settings


get_db_wrapper = asynccontextmanager(get_db)

app = FastAPI()

token_scheme = HTTPBearer()


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.get("/add/{num1}/{num2}")
def add(num1: int, num2: int):
    return {'result': num1 + num2}


app.include_router(user_router)
