from datetime import datetime, timezone, timedelta
from collections import defaultdict
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import jsonify, request
from marshmallow import Schema, fields, validate, validates_schema, ValidationError, pre_load
from . import api
from ..models import db, Subscription, Plan, PlanInterval, PlanIntervalPrice, PlanUpgrade
from app import logger


class CreateSubscriptionSchema(Schema):
    price_id = fields.UUID(required=True)

@api.route('/subscription', methods=['POST'])
@jwt_required()
def create_subscription():
    schema = CreateSubscriptionSchema()

    current_user_id = get_jwt_identity()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    query = (
            db.session.query(
                PlanInterval,
                PlanIntervalPrice,
                Plan,
            )
            .join(PlanIntervalPrice, PlanInterval.id == PlanIntervalPrice.interval_id)
            .join(Plan, Plan.id == PlanInterval.plan_id)
            .filter(PlanInterval.is_active == True)
            .filter(PlanIntervalPrice.is_active == True)
            .filter(Plan.is_active == True)
            .filter(PlanIntervalPrice.id == str(data['price_id']))
        )


    res  = query.first()
    if not res:
        return jsonify({"message": "the price id was not found"}), 404


    plan_interval, plan_inteval_price, plan = res
    

    existing_active_subscription = Subscription.find_by_params(plan_id = plan.id, user_id=current_user_id , status = 'active')
    if existing_active_subscription:
        return jsonify({"message": f"You have an active subscription with this plan"}), 400

    new_subscription = Subscription()
    new_subscription.user_id = current_user_id
    new_subscription.plan_id = plan.id
    new_subscription.price_id = plan_inteval_price.id
    new_subscription.interval = plan_interval.interval
    new_subscription.current_period_start = datetime.now(timezone.utc)

    plan_interval_days = Plan.get_interval_days(plan_interval.interval, plan_interval.interval_count)

    new_subscription.current_period_end = new_subscription.current_period_start + plan_interval_days

    new_subscription.status = 'active'
    new_subscription.amount_paid = plan_inteval_price.amount
    new_subscription.upgraded_from_subscription_id = None
    new_subscription.save_to_db()


    return jsonify({"message": "Subscription created", "data": new_subscription.to_dict()}), 201


class UpgradeSubscriptionSchema(Schema):
    subscription_id = fields.UUID(required=True)
    new_price_id = fields.UUID(required=True)

@api.route('/subscription_upgrade', methods=['PATCH'])
@jwt_required()
def upgrade_subcription():

    schema = UpgradeSubscriptionSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    current_user_id = get_jwt_identity()

    existing_active_subscription = Subscription.find_by_params(id = str(data['subscription_id']), user_id=current_user_id , status = 'active')
    if not existing_active_subscription:
        return jsonify({"message": f"the subscription was not found"}), 400

    if existing_active_subscription.upgraded_from_subscription_id:
        return jsonify({"message": f"You have already upgraded this subscription"}), 400

    if existing_active_subscription.interval == 'one_time':
        return jsonify({"message": "You cannot upgrade a one-time subscription"}), 400

    query = (
            db.session.query(
                PlanInterval,
                PlanIntervalPrice,
                Plan,
            )
            .join(PlanIntervalPrice, PlanInterval.id == PlanIntervalPrice.interval_id)
            .join(Plan, Plan.id == PlanInterval.plan_id)
            .filter(PlanInterval.is_active == True)
            .filter(PlanIntervalPrice.is_active == True)
            .filter(Plan.is_active == True)
            .filter(PlanIntervalPrice.id == str(data['new_price_id']))
        )

    res  = query.first()
    if not res:
        return jsonify({"message": "the price id was not found"}), 404


    new_plan_interval, new_plan_inteval_price, new_plan = res


    if new_plan.id == existing_active_subscription.plan_id:
        return jsonify({"message": "You are already subscribed to this plan"}), 400

    if existing_active_subscription.interval != new_plan_interval.interval:
        return jsonify({"message": "You cannot upgrade between different billing intervals"}), 400

    
    is_plan_upgradeable = PlanUpgrade.find_by_params(old_plan_id=existing_active_subscription.plan_id, new_plan_id=new_plan.id, is_active=True)
    if not is_plan_upgradeable:
        return jsonify({"message": "You cannot upgrade between these plans"}), 400

    if new_plan_inteval_price.amount < existing_active_subscription.amount_paid:
        return jsonify({"message": "You cannot downgrade to a cheaper plan"}), 400

    new_subscription = Subscription()
    new_subscription.user_id = current_user_id
    
    new_subscription.plan_id = new_plan.id
    new_subscription.price_id = new_plan_inteval_price.id
    new_subscription.current_period_start = datetime.now(timezone.utc)


    new_subscription.current_period_end = new_subscription.current_period_start  + Plan.get_interval_days(new_plan_interval.interval, new_plan_interval.interval_count)
    new_subscription.status = 'active'

    total_subscription_days= (existing_active_subscription.current_period_end - existing_active_subscription.current_period_start).days

    amount_paid_per_day = existing_active_subscription.amount_paid / total_subscription_days
    days_left = (existing_active_subscription.current_period_end.replace(tzinfo=timezone.utc)- datetime.now(timezone.utc)).days
    if days_left <= 0:
        return jsonify({"message": "You cannot upgrade a subscription that has already ended"}), 400



    new_subscription.amount_paid = int(new_plan_inteval_price.amount - (amount_paid_per_day * days_left))
    new_subscription.interval = new_plan_interval.interval

    new_subscription.upgraded_from_subscription_id = existing_active_subscription.id
    new_subscription.save_without_commit()
    existing_active_subscription.status = 'ended'
    existing_active_subscription.ended_at = datetime.now(timezone.utc)
    existing_active_subscription.save_without_commit()
    new_subscription.save_to_db()



    return jsonify({"message": "Successfully upgraded subscription", "subscription":new_subscription.to_dict()} ), 200



class CancelSubscriptionSchema(Schema):
    subscription_id = fields.UUID(required=True)

@api.route('/subscription', methods=['PATCH'])
@jwt_required()
def cancel_sbscription():

    schema = CancelSubscriptionSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    current_user_id = get_jwt_identity()

    existing_subscription = Subscription.find_by_params(id = str(data['subscription_id']), user_id=current_user_id)
    if existing_subscription.canceled_at or existing_subscription.ended_at:
        return jsonify({"message": f"the subscription is not currently active"}), 400


    existing_subscription.canceled_at = datetime.now(timezone.utc)
    existing_subscription.save_to_db()

    return jsonify({"message": "Successfully canceled subscription", "subscription":existing_subscription.to_dict()} ), 200


@api.route('/subscription', methods=['GET'])
@jwt_required()
def get_subscriptions():


    current_user_id = get_jwt_identity()

    filter = {'user_id': current_user_id}

    if request.args.get('status'):
        filter['status'] = request.args.get('status')
    if request.args.get('plan_id'):
        filter['plan_id'] = request.args.get('plan_id')

    subscriptions = Subscription.find_all_by_params( **filter)

    result = []

    for subscription in subscriptions:
        result.append(subscription.to_dict())

    return jsonify({"message": "Successfully retrieved subscription", "subscriptions":result} ), 200
