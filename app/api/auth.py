import datetime
from flask_jwt_extended import create_access_token
from flask import jsonify, request, current_app
from datetime import datetime, timedelta, timezone
from marshmallow import Schema, fields, validate, ValidationError, pre_load
from werkzeug.security import generate_password_hash, check_password_hash
from . import api
from ..models import User
from app import logger


class SignupSchema(Schema):
    first_name = fields.Str(required=True, validate=validate.Length(min=1))
    last_name = fields.Str(required=True, validate=validate.Length(min=1))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))

    @pre_load
    def strip_strings(self, data, **kwargs):
        return {
            key: value.strip() if isinstance(value, str) else value
            for key, value in data.items()
        }

@api.route('/auth/register', methods=['POST'])
def signup_user():
    schema = SignupSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    existing_user = User.find_by_email(data['email'])
    if existing_user:
        return jsonify({"message": "User with this email already exists"}), 400

    new_user = User(**data) 
    new_user.email = data['email'].lower() 
    new_user.password = generate_password_hash(data['password'])
    try:
        new_user.save_to_db()
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({"message": "your request could not be processed at this time"}), 500

    return jsonify({"message": "User created", "data": new_user.to_dict()}), 201


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=1))

    @pre_load
    def strip_strings(self, data, **kwargs):
        return {
            key: value.strip() if isinstance(value, str) and key == 'email' else value
            for key, value in data.items()
        }

@api.route('/auth/login', methods=['POST'])
def login_user():
    schema = LoginSchema()

    try:
        data = schema.load(request.json)
    except ValidationError as err:
        return jsonify(err.messages), 400

    existing_user = User.find_by_email(data['email'])
    if not existing_user:
        return jsonify({"message": "Invalid email or password"}), 401

    if not check_password_hash(existing_user.password, data['password']):
        return jsonify({"message": "Invalid email or password"}), 401

    token = create_access_token(identity=existing_user.id, expires_delta=timedelta(hours=1))

    return jsonify({"message": "login successful", "token": token }), 200
