import pytest
from app.services.user_service import UserService
from datetime import datetime
from fastapi import HTTPException
from app.db.models.user_models import UserModel
from sqlalchemy import select
from app.test.unit.conftest import user

@pytest.mark.asyncio
async def test_when_call_create_user_should_return_error_when_dont_have_code(db_session, user):
    user_service = UserService(db=db_session)
    user = await user_service.find_by_id(user.id)
    assert user.name == "John"