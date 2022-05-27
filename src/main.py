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
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False
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


# ARREGLAR y solucionar borrar usuario
# Manda todos los usuarios registrados
# Manda un solo usuario, modifica datos del usuario o borra un usuario
@app.route("/user", methods=["GET"])
@app.route("/user/<int:user_id>", methods=["GET", "PUT", "DELETE"])
@jwt_required()
def handle_users(user_id=None):
    body = request.json

    email = body.get("email", None)
    current_user_id = get_jwt_identity()

    if email is None:
        return jsonify({"msg": "Received an incomplete request."})

    user_to_update = User.query.filter_by(id=current_user_id).one_or_none()

    if user_to_update is not None:
        return jsonify({"msg": "User not found."}), 404

    user_response = User.update_email(user_to_update)

    if isinstance(user_response, str):
        return jsonify({"msg": user_response}), 404
    else:
        new_user = user_response.serialize()

    return jsonify({"response": new_user}), 204


# Crea 3 controladores con sus SN
@app.route("/populate", methods=["POST"])
def handle_populate():
    for i in range(1, 4):
        Controller.new_controller(controller_sn=f"000{i}")

    return jsonify({"msg": "Populated controllers."})


# Verifica que el controlador este registrado, y si lo esta, le manda el token del usuario
@app.route("/validate", methods=["POST"])
def handle_validation():
    body = request.json
    controller_sn = body["controller_sn"]

    controller_exists = Controller.query.filter_by(
        controller_sn=controller_sn
    ).one_or_none()

    if controller_exists is None:
        return jsonify({"response": "Controller serial number is incorrect."}), 404

    if not controller_exists.user_id:
        return jsonify({"response": "Controller has not been registered."}), 404

    owner = User.query.filter_by(id=controller_exists.user_id).first()

    return jsonify({"response": f"{owner.token}"}), 200


# Registra al usuario en la bd, recibe nombre, email y contraseña
@app.route("/signup", methods=["POST"])
def handle_signup():
    body = request.json

    name = body.get("name")
    email = body.get("email")
    password = body.get("password")
    controller_sn = body.get("controller_sn")

    if not email or not name or not password or not controller_sn:
        return jsonify({"msg": "Received an incomplete request."}), 400

    user_exists = User.query.filter_by(email=email).one_or_none()
    if user_exists is not None:
        return jsonify({"msg": "User email already registered."}), 404

    user_controller = Controller.query.filter_by(controller_sn=controller_sn).first()
    if not user_controller:
        return jsonify({"msg": "Controller id not recognized."}), 404
    if user_controller.user_id:
        return jsonify({"msg": "Controller id already assigned to a user."}), 404

    user_response = User.new_user(
        name=name,
        email=email,
        password=password,
    )

    if isinstance(user_response, str):
        return jsonify({"msg": user_response}), 404
    else:
        user = user_response.serialize()

    user_created = User.query.filter_by(email=body["email"]).first()

    controller_to_update = Controller.query.filter_by(
        controller_sn=controller_sn
    ).first()

    assignment_response = Controller.assign_user(
        controller=controller_to_update, user_id=user_created.id
    )

    if isinstance(assignment_response, str):
        return jsonify({"msg": assignment_response}), 404
    else:
        controller = assignment_response.serialize()

    return jsonify({"user": user, "controller": controller}), 201


# Recibe email y contraseña, verifica en la bd y manda un token de vuelta
@app.route("/login", methods=["POST"])
def handle_login():
    body = request.json

    if not body.get("email") or not body.get("password"):
        return jsonify({"msg": "Received an incomplete request."}), 404

    user = User.query.filter_by(
        email=body.get("email"), password=body.get("password")
    ).one_or_none()

    if user is None:
        return jsonify({"msg": "Incorrect email or password."}), 404

    token = create_access_token(identity=user.id)
    saved_token = User.save_token(user, token)

    if isinstance(saved_token, str):
        return jsonify({"msg": saved_token}), 404

    return jsonify({"token": token, "user_id": user.id, "email": user.email})


# Manda todas las entradas de un usuario específico
# Manda las entradas de un solo dispositivo del usuario
@app.route("/entries", methods=["GET"])
@app.route("/entries/<string:device_name>", methods=["GET"])
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


# Crea una nueva entrada en la base de datos a modo de prueba
@app.route("/create", methods=["POST"])
@jwt_required()
def handle_create():
    body = request.json
    current_user_id = get_jwt_identity()

    device_type = body["device_type"]
    device_data = body["device_data"]

    devices = ["sonar", "motion", "thermostat", "light"]
    if device_type not in devices:
        return jsonify({"msg": "Device type not recognized."}), 404

    last_entry = (
        Entries.query.filter_by(user_id=current_user_id, device_type=device_type)
        .order_by(Entries.date_created.desc())
        .first()
    )

    if last_entry is not None:
        if device_data == last_entry.device_data:
            return jsonify({"response": last_entry.serialize()}), 200

    entry_response = Entries.new_entry(  # CHECK
        user_id=current_user_id,
        device_type=device_type,
        device_data=device_data,
    )

    if isinstance(entry_response, str):
        return jsonify({"msg": entry_response}), 404
    else:
        entry = entry_response.serialize()

    return jsonify({"response": entry}), 201


# this only runs if `$ python src/main.py` is executed
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=PORT, debug=False)
