# tests/conftest.py

import pytest
import os
import sys
from flask_jwt_extended import create_access_token
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db as _db
from app.models import User, Plan, PlanInterval, PlanIntervalPrice, Subscription

@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(scope="function")
def db(app):
    yield _db

@pytest.fixture
def auth_headers(access_token):
    return {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

@pytest.fixture
def active_plan(app):
    plan = Plan(name="Basic Plan", is_active=True, description="Premium plan")
    _db.session.add(plan)
    _db.session.commit()
    return plan

@pytest.fixture
def active_plan_interval(app, active_plan):
    interval = PlanInterval(plan_id=active_plan.id, interval="month", interval_count=1, is_active=True)
    _db.session.add(interval)
    _db.session.commit()
    return interval

@pytest.fixture
def active_price(app, active_plan_interval):
    price = PlanIntervalPrice(interval_id=active_plan_interval.id, amount=1000, currency='USD', is_active=True)
    _db.session.add(price)
    _db.session.commit()
    return price

@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User(
            first_name="testuser",
            last_name="testuser",
            email="test@example.com",
            password="testpassword"  # Or hashed
        )
        _db.session.add(user)
        _db.session.commit()
        yield user
        # _db.session.delete(user)
        # _db.session.commit()

@pytest.fixture
def jwt_headers(test_user):
    token = create_access_token(identity=test_user.id)
    return {
        "Authorization": f"Bearer {token}"
    }

@pytest.fixture
def active_plan_setup(db):
    plan = Plan(name="Standard Plan", is_active=True, description="Premium plan")
    _db.session.add(plan)
    _db.session.flush()

    interval = PlanInterval(plan_id=plan.id, interval="month", interval_count=1, is_active=True)
    _db.session.add(interval)
    _db.session.flush()

    price = PlanIntervalPrice(interval_id=interval.id, amount=1000, currency='USD', is_active=True)
    _db.session.add(price)
    _db.session.commit()

    return plan, interval, price



@pytest.fixture
def active_subscription(app, test_user, active_plan, active_price, active_plan_interval):
    subscription = Subscription(
        user_id=test_user.id,
        plan_id=active_plan.id,
        price_id=active_price.id,
        interval=active_plan_interval.interval,
        current_period_start=datetime.now(timezone.utc),
        current_period_end=datetime.now(timezone.utc) + timedelta(days=30),
        status='active',
        amount_paid=1000
    )
    _db.session.add(subscription)
    _db.session.commit()
    return subscription