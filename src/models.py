from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Base(db.Model):
    __abstract__ = True
    date_created = db.Column(
        db.DateTime(timezone=True), default=db.func.now(), nullable=False
    )


class Controller(Base):
    id = db.Column(db.Integer, primary_key=True)
    controller_sn = db.Column(db.Integer, unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    def assign_user(controller_sn, user_id):
        controller_to_update = Controller.query.filter_by(
            controller_sn=controller_sn
        ).first()

        controller_to_update.user_id = user_id
        try:
            db.session.commit()
            return controller_to_update
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


class User(Base):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    controller_sn = db.relationship("Controller", backref="owner", uselist=False)
    entries = db.relationship("Entries", backref="author", uselist=True)

    def __repr__(self):
        return "<User %r>" % self.id

    @classmethod
    def new_user(cls, name, email, password, controller_sn):
        instance = cls(name=name, email=email, password=password)

        if isinstance(instance, cls):
            user_exists = User.query.filter_by(email=instance.email).one_or_none()

            if user_exists is not None:
                return "User email already registered."

            user_controller = Controller.query.filter_by(
                controller_sn=controller_sn
            ).one_or_none()

            if user_controller is not None:
                if user_controller.user_id:
                    return "Controller id already assigned to a user."

                db.session.add(instance)
                try:
                    db.session.commit()
                    return instance
                except Exception as error:
                    db.session.rollback()
                    print(error.args)
            else:
                return "Controller id not recognized."
        return "Could not create user."

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
        devices = ["tank", "motion", "temperature", "light"]
        instance = cls(**kwargs)

        if isinstance(instance, cls):
            if instance.device_type not in devices:
                return "Device type not recognized."

            last_entry = (
                Entries.query.filter_by(
                    user_id=instance.user_id, device_type=instance.device_type
                )
                .order_by(Entries.date_created.desc())
                .first()
            )

            if last_entry is not None:
                if instance.device_data == last_entry.device_data:
                    return last_entry
                else:
                    db.session.add(instance)
                    try:
                        db.session.commit()
                        return instance
                    except Exception as error:
                        db.session.rollback()
                        print(error.args)
            else:
                db.session.add(instance)
                try:
                    db.session.commit()
                    return instance
                except Exception as error:
                    db.session.rollback()
                    print(error.args)
        return "Could not create instance."

    def serialize(self):
        return {
            "entry_id": self.id,
            "user_id": self.user_id,
            "date_created": self.date_created,
            "device_type": self.device_type,
            "device_data": self.device_data,
        }
