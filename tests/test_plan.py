from app.models import Plan


def test_create_plan_success(client, db, jwt_headers):
    payload = {
        "name": "Premium Plan",
        "description": "Best plan for professionals",
        "intervals": [
            {
                "interval": "month",
                "interval_count": 1,
                "prices": [
                    {"currency": "USD", "amount": 1000}
                ]
            }
        ]
    }
    response = client.post("/api/v1/plan", json=payload, headers=jwt_headers)
    assert response.status_code == 201


def test_create_plan_duplicate_name(client, db, jwt_headers):
    existing_plan = Plan(name="Basic", description="desc")
    db.session.add(existing_plan)
    db.session.commit()

    payload = {
        "name": "Basic",
        "description": "Best plan for students",
        "intervals": [
            {
                "interval": "month",
                "interval_count": 1,
                "prices": [
                    {"currency": "USD", "amount": 1000}
                ]
            }
        ]
    }
    response = client.post("/api/v1/plan", json=payload, headers=jwt_headers)
    assert response.status_code == 400 
    assert "already exists" in response.get_data(as_text=True)


def test_create_plan_duplicate_currency(client, jwt_headers):
    payload = {
        "name": "Standard Plan",
        "intervals": [
            {
                "interval": "month",
                "interval_count": 1,
                "prices": [
                    {"currency": "USD", "amount": 1000},
                    {"currency": "USD", "amount": 1500}
                ]
            }
        ]
    }
    response = client.post("/api/v1/plan", json=payload, headers=jwt_headers)
    assert response.status_code == 400
    assert "Duplicate currency found" in response.get_data(as_text=True)


def test_get_all_plans(client, db, jwt_headers):
    payload = {
        "name": "Basic",
        "description": "Best plan for students",
        "intervals": [
            {
                "interval": "month",
                "interval_count": 1,
                "prices": [
                    {"currency": "USD", "amount": 1000}
                ]
            }
        ]
    }
    response = client.post("/api/v1/plan", json=payload, headers=jwt_headers)

    response = client.get("/api/v1/plan", headers=jwt_headers)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data['plans'], list)
