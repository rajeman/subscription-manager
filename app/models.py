import uuid
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.orm import relationship
from sqlalchemy import (Column, String, Text,DECIMAL, Integer, Boolean, Enum, Index, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, func)
from datetime import datetime, timezone
from . import db




class BaseModel(db.Model):
    """Base data model for all objects"""
    __abstract__ = True
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def save_all_without_commit(self):
        db.session.add_all(self)
        db.session.commit()

    def save_without_commit(self):        
        db.session.add(self)

    def commit(self):
        db.session.commit()



class User(BaseModel):
    __tablename__ = 'users'
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)
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


    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    def update_last_login(self):
        self.last_login = datetime.now(timezone.utc)
        self.save_to_db()


class Plan(BaseModel):
    __tablename__ = 'plans'

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    intervals = relationship('PlanInterval', back_populates='plan', cascade='all, delete-orphan')


    __table_args__ = (
        Index(
            'plan_unique_name_content',
            'name',
            unique=True
        ),
    )

    @classmethod
    def find_by_name(cls, name):
        return cls.query.filter_by(name=name).first()

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
            # "intervals": [interval.to_dict() for interval in self.intervals]  # Serialize plan intervals
        }



class PlanInterval(BaseModel):
    __tablename__ = 'plan_intervals'

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = Column(CHAR(36), ForeignKey('plans.id'), nullable=False)

    interval = Column(Enum( 'one_time', 'day', 'week', 'month', 'year'), nullable=False)
    interval_count = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)

    plan = relationship('Plan', back_populates='intervals')

    prices = relationship('PlanIntervalPrice', back_populates='interval', cascade='all, delete-orphan')


    __table_args__ = (
        UniqueConstraint('id','plan_id', name='unique_plan_interval_plan_id'),
        CheckConstraint('interval_count >= 0', name='check_interval_count_non_zero'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "interval": self.interval,
            "interval_count": self.interval_count,
            "is_active": self.is_active,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
            # "prices": [price.to_dict() for price in self.prices]  # Serialize plan interval prices
        }

class PlanIntervalPrice(BaseModel):
    __tablename__ = 'plan_interval_prices'

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    interval_id = Column(CHAR(36), ForeignKey('plan_intervals.id'), nullable=False)
    currency = Column(CHAR(3), nullable=False) 
    amount = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)


    interval = relationship('PlanInterval', back_populates='prices')


    __table_args__ = (
        UniqueConstraint('interval_id', 'currency', name='uq_interval_currency'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "interval_id": self.interval_id,
            "currency": self.currency,
            "amount": self.amount,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
        }