import json
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.queries.user_queries import UserQueries
from fastapi import HTTPException, status
from datetime import datetime


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db            

    async def find_by_user_auth_id(self, user_auth_id: str):
        user_queries = UserQueries(session=self.db)
        user = await user_queries.find_by_user_auth_id(user_auth_id=user_auth_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para acceder a este recurso")
        return user
            
    async def find_by_id(self, id: int):
        user_queries = UserQueries(session=self.db)
        user = await user_queries.find_by_id(id=id)
        if not user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para acceder a este recurso")
        return user
