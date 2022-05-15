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
    User,
    Entries,
    Electricity,
    Voltage,
    Motion,
    Temperature,
    Light,
    Tank,
)

# from models import Person

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


# GET ALL USERS, GET A SINGLE USER, MODIFY OR DELETE A SINGLE USER


@app.route("/user", methods=["GET"])
@app.route("/user/<int:user_id>", methods=["GET", "PUT", "DELETE"])
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


# CREATE NEW USER


@app.route("/signup", methods=["POST"])
def handle_signup():
    body = request.json

    if not body.get("name") or not body.get("email") or not body.get("password"):
        return jsonify({"msg": "Not found."}), 404
    else:
        user = User(name=body["name"], email=body["email"], password=body["password"])
        db.session.add(user)

        try:
            db.session.commit()
            return jsonify(user.serialize()), 201
        except Exception as error:
            db.session.rollback()
            return jsonify(error.args), 500


# USER LOGIN AND TOKEN CREATION


@app.route("/login", methods=["POST"])
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


# GET ALL USER ENTRIES, GET ALL USER ENTRIES FOR A SPECIFIC DEVICE


@app.route("/entries", methods=["GET"])
@app.route("/entries/<string:device_name>", methods=["GET"])
@jwt_required()
def handle_entries(device_name=None):
    current_user_id = get_jwt_identity()

    if request.method == "GET":
        if device_name is None:
            all_entries = Entries.query.filter_by(user_id=current_user_id).all()
            all_entries = list(map(lambda ntr: ntr.serialize(), all_entries))
            return jsonify({"results": all_entries})
        else:
            device_entries = Entries.query.filter_by(
                user_id=current_user_id, device=device_name
            ).all()
            device_entries = list(map(lambda ntr: ntr.serialize(), device_entries))
            return jsonify({"results": device_entries})


# this only runs if `$ python src/main.py` is executed
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=PORT, debug=False)
