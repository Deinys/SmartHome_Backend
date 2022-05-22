from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Controller(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    controller_sn = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    @classmethod
    def new_controller(cls, **kwargs):
        instance = cls(**kwargs)

        if isinstance(instance, cls):
            try:
                db.session.add(instance)
                db.session.commit()
                return instance
            except Exception as error:
                db.session.rollback()
                print(error.args)
        return "Could not create controller."

    def assign_user(controller, user_id):
        try:
            controller.user_id = user_id
            db.session.commit()
            return controller
        except Exception as error:
            db.session.rollback()
            print(error.args)
        return "Could not assign user."

    def serialize(self):
        return {
            "controller_id": self.id,
            "controller_sn": self.controller_sn,
            "user_id": self.user_id,
        }


class Base(db.Model):
    __abstract__ = True
    date_created = db.Column(
        db.DateTime(timezone=True), default=db.func.now(), nullable=False
    )


class User(Base):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    token = db.Column(db.String(500), unique=True)
    controller_sn = db.relationship("Controller", backref="owner", uselist=False)
    entries = db.relationship("Entries", backref="author", uselist=True)

    def __repr__(self):
        return "<User %r>" % self.id

    @classmethod
    def new_user(cls, **kwargs):
        instance = cls(**kwargs)

        if isinstance(instance, cls):
            try:
                db.session.add(instance)
                db.session.commit()
                return instance
            except Exception as error:
                db.session.rollback()
                print(error.args)
        return "Could not create user."

    def save_token(user, token):
        try:
            user.token = token
            db.session.commit()
            return user
        except Exception as error:
            db.session.rollback()
            print(error.args)
        return "Could not save token."

    def serialize(self):
        return {
            "user_id": self.id,
            "name": self.name,
            "email": self.email,
            "date_created": self.date_created,
        }


class Entries(Base):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    device_type = db.Column(db.String(40), nullable=False)
    device_data = db.Column(db.String(250), nullable=False)

    @classmethod
    def new_entry(cls, **kwargs):
        instance = cls(**kwargs)

        if isinstance(instance, cls):
            try:
                db.session.add(instance)
                db.session.commit()
                return instance
            except Exception as error:
                db.session.rollback()
                print(error.args)
        return "Could not create entry."

    def serialize(self):
        return {
            "entry_id": self.id,
            "user_id": self.user_id,
            "date_created": self.date_created,
            "device_type": self.device_type,
            "device_data": self.device_data,
        }
