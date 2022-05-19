"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from models import (
    db,
    Controller,
    User,
    Entries,
)


app = Flask(__name__)
app.url_map.strict_slashes = False
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DB_CONNECTION_STRING")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.environ.get("FLASK_API_KEY")
jwt = JWTManager(app)

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code


# generate sitemap with all your endpoints
@app.route("/")
def sitemap():
    return generate_sitemap(app)


@app.route("/user", methods=["GET"])  # Manda todos los usuarios registrados
@app.route(
    "/user/<int:user_id>", methods=["GET", "PUT", "DELETE"]
)  # Manda un solo usuario, modifica datos del usuario o borra un usuario
@jwt_required()
def handle_users(user_id=None):
    if request.method == "GET":
        if user_id is None:
            all_users = User.query.all()
            all_users = list(map(lambda usr: usr.serialize(), all_users))
            return jsonify({"results": all_users}), 200
        else:
            user_to_send = User.query.filter_by(id=user_id).one_or_none()

            if user_to_send is not None:
                return jsonify(user_to_send.serialize()), 200
            else:
                return jsonify({"msg": "Not found."}), 404

    if request.method == "PUT":
        body = request.json
        email = body.get("email", None)

        if email is not None:
            user_to_update = User.query.filter_by(id=user_id).first()

            if user_to_update is not None:
                user_to_update.email = email

                try:
                    db.session.commit()
                    return jsonify(user_to_update.serialize()), 201
                except Exception as error:
                    db.session.rollback()
                    return jsonify(error.args)
        else:
            return jsonify({"msg": "Not found."}), 404

    if request.method == "DELETE":
        user_to_delete = User.query.filter_by(id=user_id).first()

        if user_to_delete is not None:
            db.session.delete(user_to_delete)

            try:
                db.session.commit()
                return jsonify([]), 204
            except Exception as error:
                db.session.rollback()
                return jsonify(error.args)
        else:
            return jsonify({"msg": "Not found."}), 404

    return "You should not be seeing this message /user"


@app.route(
    "/signup", methods=["POST"]
)  # Registra al usuario en la bd, recibe nombre, email y contraseña
def handle_signup():
    body = request.json

    if (
        not body.get("name")
        or not body.get("email")
        or not body.get("password")
        or not body.get("controller_sn")
    ):
        return jsonify({"msg": "Received an incomplete request."}), 404
    else:
        user_response = User.new_user(
            name=body["name"],
            email=body["email"],
            password=body["password"],
            controller_sn=body["controller_sn"],
        )

        if isinstance(user_response, str):
            return jsonify({"msg": user_response}), 404

        user_created = User.query.filter_by(email=body["email"]).first()

        assignment_response = Controller.assign_user(
            controller_sn=body["controller_sn"], user_id=user_created.id
        )

        if isinstance(assignment_response, str):
            return jsonify({"msg": assignment_response}), 404

        user = user_response.serialize()
        controller = assignment_response.serialize()

        return jsonify({"user": user, "controller": controller}), 201


@app.route(
    "/login", methods=["POST"]
)  # Recibe email y contraseña, verifica en la bd y manda un token de vuelta
def handle_login():
    body = request.json

    if not body.get("email") or not body.get("password"):
        return jsonify({"msg": "Not found."}), 404
    else:
        user = User.query.filter_by(
            email=body.get("email"), password=body.get("password")
        ).one_or_none()

        if user is not None:
            token = create_access_token(identity=user.id)
            return jsonify({"token": token, "user_id": user.id, "email": user.email})
        else:
            return jsonify({"msg": "Not found."}), 404

    return "You should not be seeing this message /login"


@app.route(
    "/entries", methods=["GET"]
)  # Manda todas las entradas de un usuario específico
@app.route(
    "/entries/<string:device_name>", methods=["GET"]
)  # Manda las entradas de un solo dispositivo del usuario
@jwt_required()
def handle_entries(device_name=None):
    current_user_id = get_jwt_identity()

    if request.method == "GET":
        if device_name is None:
            all_entries = Entries.query.filter_by(user_id=current_user_id).all()
            all_entries = list(map(lambda ntr: ntr.serialize(), all_entries))

            return jsonify({"results": all_entries}), 200
        else:
            device_entries = Entries.query.filter_by(
                user_id=current_user_id, device_type=device_name
            ).all()
            device_entries = list(map(lambda ntr: ntr.serialize(), device_entries))

            return jsonify({"results": device_entries}), 200


@app.route(
    "/create", methods=["POST"]
)  # Crea una nueva entrada en la base de datos a modo de prueba
@jwt_required()
def handle_create():
    body = request.json
    current_user_id = get_jwt_identity()

    entry_response = Entries.new_entry(
        user_id=current_user_id,
        device_type=body["device_type"],
        device_data=body["device_data"],
    )

    if entry_response is not None:
        entry = entry_response.serialize()
        return jsonify({"entry": entry}), 201
    else:
        return (
            jsonify({"msg": entry_response}), 404
        )


# this only runs if `$ python src/main.py` is executed
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=PORT, debug=False)
