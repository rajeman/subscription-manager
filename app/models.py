import uuid
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy import (Column, String, Index, DateTime, func)
from datetime import datetime
from . import db




class BaseModel(db.Model):
    """Base data model for all objects"""
    __abstract__ = True

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def save_without_commit(self):
        db.session.add(self)


class User(BaseModel):
    __tablename__ = 'users'
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime, nullable=True)

    __table_args__ = (
            Index(
                'user_unique_email_content',
                'email',
                unique=True
                ),
        )

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
            "last_login": self.last_login.strftime("%Y-%m-%d %H:%M:%S") if self.last_login else None,
        }

    @classmethod
    def find_by_id(cls, id):
        return cls.query.filter_by(id=id).first()


    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()
