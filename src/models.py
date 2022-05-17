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
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    device = db.Column(db.String(40), nullable=False)
    data = db.Column(db.String(250), nullable=False)

    @classmethod
    def new_entry(cls, **kwargs):
        devices = ["tank", "motion", "temperature", "light"]
        instance = cls(**kwargs)

        if isinstance(instance, cls):
            if instance.device not in devices:
                print(f"Device type not recognized. Device is {instance.device}.")
                return None

            last_entry = (
                Entries.query.filter_by(
                    user_id=instance.user_id, device=instance.device
                )
                .order_by(Entries.created.desc())
                .first()
            )

            if last_entry is not None:
                if instance.data == last_entry.data:
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
        else:
            print("Could not create instance.")
            return None

    def serialize(self):
        return {
            "id": self.id,
            "user": self.user_id,
            "created": self.created,
            "device": self.device,
            "data": self.data,
        }
