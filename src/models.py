from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Base(db.Model):
    __abstract__ = True
    created = db.Column(
        db.DateTime(timezone=True), default=db.func.now(), nullable=False
    )


class User(Base):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), unique=False, nullable=False)
    image = db.Column(db.String(30), nullable=False, default="default.jpg")
    entries = db.relationship("Entries", backref="author", uselist=True)

    def __repr__(self):
        return "<User %r>" % self.id

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
        }


class Entries(Base):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.Boolean, nullable=False, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    data = db.Column(db.String(250), nullable=False)
    device = db.Column(db.String(40), nullable=False)

    __mapper_args = {"polymorphic_identity": "entry", "polymorphic_on": device}

    def serialize(self):
        return {
            "entry_id": self.id,
            "entry_date": self.created,
            "entry_device": self.device,
            "entry_data": self.data,
            "device_status": self.status
        }


class Electricity(Entries):
    id = db.Column(db.Integer, db.ForeignKey("entries.id"), primary_key=True)

    __mapper_args__ = {"polymorphic_identity": "electricity"}

    @classmethod
    def create(cls, data):
        instance = cls(**data)
        if isinstance(instance, cls):
            db.session.add(instance)
            try:
                db.session.commit()
                return instance
            except Exception as error:
                db.session.rollback()
                print(error.args)
        else:
            print("Couldn't create instance.")
            return None



class Voltage(Entries):
    id = db.Column(db.Integer, db.ForeignKey("entries.id"), primary_key=True)

    __mapper_args__ = {"polymorphic_identity": "voltage"}

    @classmethod
    def create(cls, data):
        instance = cls(**data)
        if isinstance(instance, cls):
            db.session.add(instance)
            try:
                db.session.commit()
                return instance
            except Exception as error:
                db.session.rollback()
                print(error.args)
        else:
            print("Couldn't create instance.")
            return None


class Motion(Entries):
    id = db.Column(db.Integer, db.ForeignKey("entries.id"), primary_key=True)

    __mapper_args__ = {"polymorphic_identity": "motion"}

    @classmethod
    def create(cls, data):
        instance = cls(**data)
        if isinstance(instance, cls):
            db.session.add(instance)
            try:
                db.session.commit()
                return instance
            except Exception as error:
                db.session.rollback()
                print(error.args)
        else:
            print("Couldn't create instance.")
            return None


class Temperature(Entries):
    id = db.Column(db.Integer, db.ForeignKey("entries.id"), primary_key=True)

    __mapper_args__ = {"polymorphic_identity": "temperature"}

    @classmethod
    def create(cls, data):
        instance = cls(**data)
        if isinstance(instance, cls):
            db.session.add(instance)
            try:
                db.session.commit()
                return instance
            except Exception as error:
                db.session.rollback()
                print(error.args)
        else:
            print("Couldn't create instance.")
            return None


class Light(Entries):
    id = db.Column(db.Integer, db.ForeignKey("entries.id"), primary_key=True)

    __mapper_args__ = {"polymorphic_identity": "light"}

    @classmethod
    def create(cls, data):
        instance = cls(**data)
        if isinstance(instance, cls):
            db.session.add(instance)
            try:
                db.session.commit()
                return instance
            except Exception as error:
                db.session.rollback()
                print(error.args)
        else:
            print("Couldn't create instance.")
            return None


class Tank(Entries):
    id = db.Column(db.Integer, db.ForeignKey("entries.id"), primary_key=True)

    __mapper_args__ = {"polymorphic_identity": "tank"}

    @classmethod
    def create(cls, data):
        instance = cls(**data)
        if isinstance(instance, cls):
            db.session.add(instance)
            try:
                db.session.commit()
                return instance
            except Exception as error:
                db.session.rollback()
                print(error.args)
        else:
            print("Couldn't create instance.")
            return None
