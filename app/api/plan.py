from collections import defaultdict
from flask_jwt_extended import jwt_required
from flask import jsonify, request
from marshmallow import Schema, fields, validate, validates_schema, ValidationError, pre_load
from . import api
from ..models import db, Plan, PlanInterval, PlanIntervalPrice
from app import logger




def unique_currency(item):
    currencies = set()
    for t in item:
        if t['currency'] in currencies:
            raise ValidationError(f"Duplicate currency found for the same plan pricing: {t['currency']}")
        currencies.add(t['currency'] )

def unique_billing_interval(item):
    billing_intervals = set()
    for t in item:
        if t['interval'] in billing_intervals:
            raise ValidationError(f"Duplicate billing interval found: {t['interval']}")
        billing_intervals.add(t['interval'] )


class PlanPriceSchema(Schema):
    currency = fields.Str(required=True, validate=validate.Length(equal=3))
    amount = fields.Int(required=True, validate=validate.Range(min=0, error="Amount cannot be negative"))

class PlanIntervalSchema(Schema):
    interval = fields.Str(validate=validate.OneOf(["one_time", "day", "week", "month", "year"]), required=True)
    interval_count = fields.Int(validate=validate.Range(min=0, error="Interval count cannot be negative"), required=True)
    prices = fields.List(fields.Nested(PlanPriceSchema), validate=unique_currency, required=True)

class CreatePlanSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=3))
    description = fields.Str(required=True, validate=validate.Length(min=3))
    intervals = fields.List(fields.Nested(PlanIntervalSchema), required=True, validate=validate.Length(min=1, error="At least one interval is required"))

    @validates_schema
    def validate_plan_interval(self, data, **kwargs):
        intervals = set()
        for interval in data['intervals']:
            if interval['interval'] in intervals:
                raise ValidationError(f"Duplicate interval found: {interval['interval']}", "interval")
            intervals.add(interval['interval'])
            
            if interval['interval'] == "one_time" and interval['interval_count'] != 0:
                raise ValidationError("one_time plan must have an interval count of 0", "interval_count")
        
            if interval["interval"] != "one_time"  and interval["interval_count"] == 0:
                raise ValidationError("recurring plans must have an interval of at least one", "interval")



    @pre_load
    def strip_strings(self, data, **kwargs):
        return {
            key: value.strip() if isinstance(value, str) else value
            for key, value in data.items()
        }

@api.route('/plan', methods=['POST'])
@jwt_required()
def create_plan():
    schema = CreatePlanSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    existing_plan = Plan.find_by_name(data['name'])
    if existing_plan:
        return jsonify({"message": f"Plan with the name {data['name']} already exists"}), 400

    new_plan = Plan() 
    new_plan.name = data['name']
    new_plan.description = data['description']
    new_plan.save_without_commit()

    for interval_data in data['intervals']:
        plan_interval = PlanInterval(plan = new_plan)
        plan_interval.interval = interval_data['interval']
        plan_interval.interval_count = interval_data['interval_count']
        plan_interval.save_without_commit()

        for price_data in interval_data['prices']:
            price = PlanIntervalPrice(interval=plan_interval)
            price.currency =  price_data['currency'].upper()
            price.amount = price_data['amount']
            price.save_without_commit()


    try:
        new_plan.save_to_db()
    except Exception as e:
        logger.error(f"Error creating plan: {e}")
        return jsonify({"message": "your request could not be processed at this time"}), 500

    return jsonify({"message": "Plan created", "data": new_plan.to_dict()}), 201


@api.route('/plan', methods=['GET'])
@jwt_required()
def get_plans():
    currency = request.args.get('currency', type=str)
    query = (
            db.session.query(
                Plan,
                PlanInterval,
                PlanIntervalPrice,
            )
            .join(Plan, Plan.id == PlanInterval.plan_id)
            .join(PlanIntervalPrice, PlanInterval.id == PlanIntervalPrice.interval_id)
            .filter(Plan.is_active == True)
            .filter(PlanInterval.is_active == True)
            .filter(PlanIntervalPrice.is_active == True)
            )
    if currency:
        query = query.filter(PlanIntervalPrice.currency == currency)


    plans = query.all()

    output = []
    included_plans = defaultdict(list)
    for plan, interval, price in plans:
        plan_data = plan.to_dict()
        interval_data = interval.to_dict()
        price_data = price.to_dict()
        interval_data['prices'] = [price_data]
        if plan.id in included_plans:
            included_plans[plan.id]['intervals'].append(interval_data)
        else:
            included_plans[plan.id] = plan_data
            included_plans[plan.id]['intervals'] = [interval_data]
    
    output = sorted(included_plans.values(), key=lambda x: x["created_at"])
    
    return jsonify({"message": "Successfully retrieved plans", "plans":output} ), 200
