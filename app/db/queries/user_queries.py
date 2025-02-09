from sqlalchemy import func, select, update, and_, exists
from sqlalchemy.ext.asyncio import AsyncSession as Session
from app.db.models.user_model import UserModel

class UserQueries:
    def __init__(self, session: Session):
        self.session = session
    
    async def get_first_user(self):
        result = await self.session.execute(func.count(UserModel.id))
        return result.scalars().first()
    
    async def find_by_id(self, id: int):
            result = await self.session.execute(select(UserModel).where(UserModel.id == id))
            return result.scalar_one_or_none()
    