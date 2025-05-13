import time
from app.models import User, Plan, PlanInterval, PlanIntervalPrice, PlanUpgrade




def test_create_subscription_success(client, jwt_headers, test_user, active_plan_setup):
    _, _, price = active_plan_setup

    response = client.post("/api/v1/subscription", json={"price_id": str(price.id)}, headers=jwt_headers)
    assert response.status_code == 201
    data = response.get_json()
    assert data["message"] == "Subscription created"
    assert data["data"]["status"] == "active"


def test_upgrade_subscription(client, jwt_headers, active_subscription, active_plan_setup, db):
    # Create a new plan and price for upgrade
    plan = Plan(name="Premium", is_active=True, description="Premium plan")
    db.session.add(plan)
    db.session.flush()

    interval = PlanInterval(plan_id=plan.id, interval="month", interval_count=1, is_active=True)
    db.session.add(interval)
    db.session.flush()

    price = PlanIntervalPrice(interval_id=interval.id, amount=1000, currency='USD', is_active=True)
    db.session.add(price)
    db.session.commit()


    plan_upgrade = PlanUpgrade(old_plan_id=active_subscription.plan_id, new_plan_id=plan.id, is_active=True)
    db.session.add(plan_upgrade)
    db.session.commit()


    response = client.patch('/api/v1/subscription_upgrade', json={
        'subscription_id': str(active_subscription.id),
        'new_price_id': str(price.id)
    }, headers=jwt_headers)

    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Successfully upgraded subscription'
    assert 'subscription' in data
    assert data['subscription']['plan_id'] == str(plan.id)


def test_cancel_subscription(client, jwt_headers, active_subscription):
    response = client.patch('/api/v1/subscription', json={'subscription_id': str(active_subscription.id)}, headers=jwt_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Successfully canceled subscription'
    assert 'subscription' in data
    assert data['subscription']['status'] == 'active'
    assert data['subscription']['canceled_at'] is not None

def test_get_subscriptions(client, jwt_headers, active_subscription):
    response = client.get('/api/v1/subscription', headers=jwt_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Successfully retrieved subscription'
    assert 'subscriptions' in data
    assert isinstance(data['subscriptions'], list)
    assert any(sub['id'] == str(active_subscription.id) for sub in data['subscriptions'])


def test_get_subscriptions_performance(client, jwt_headers):
    start_time = time.time()
    response = client.get('/api/v1/subscription', headers=jwt_headers)
    end_time = time.time()
    duration = end_time - start_time
    assert response.status_code == 200
    assert duration < 0.5  