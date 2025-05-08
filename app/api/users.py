from flask import jsonify, request
from marshmallow import Schema, fields, validate, ValidationError
from . import api
from ..models import User


class CreateUserSchema(Schema):
    first_name = fields.Str(required=True, validate=validate.Length(min=1))
    last_name = fields.Str(required=True, validate=validate.Length(min=1))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))

@api.route('/users', methods=['POST'])
def create_user():
    schema = CreateUserSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    new_user = User(**data) 

    try:
        new_user.save_to_db()
    except Exception as e:
        return jsonify({"message": "your request could not be processed at this time"}), 500

    return jsonify({"message": "User created", "data": new_user.to_dict()}), 201
