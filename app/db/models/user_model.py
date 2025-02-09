from sqlalchemy import Column, Integer, String, Boolean
from app.db.models.common_model import Base


class UserModel(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    last_name = Column(String)
    document_number = Column(String, index=True)
    phone_number = Column(String, index=True)
    email = Column(String, index=True)
    user_auth_id = Column(String, index=True)
    accept_terms_and_conditions = Column(Boolean, default=False)
    accept_privacy_policy = Column(Boolean, default=False)

    def to_dict(model_instance):
        return None