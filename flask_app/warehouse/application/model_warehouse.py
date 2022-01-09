from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True
    creation_date = Column(DateTime(timezone=True), server_default=func.now())
    update_date = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        fields = ""
        for c in self.__table__.columns:
            if fields == "":
                fields = "{}='{}'".format(c.name, getattr(self, c.name))
            else:
                fields = "{}, {}='{}'".format(fields, c.name, getattr(self, c.name))
        return "<{}({})>".format(self.__class__.__name__, fields)

    @staticmethod
    def list_as_dict(items):
        return [i.as_dict() for i in items]

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Order(BaseModel):
    STATUS_WAITING_FOR_PAYMENT = "waiting"
    STATUS_CREATED = "created"
    STATUS_ACCEPTED = "accepted"
    STATUS_DELIVERED = "delivered"
    STATUS_CANCELLED = "cancelled"
    STATUS_PREPARING = "preparing"

    __tablename__ = "manufacturing_order"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, nullable=False)
    number_of_pieces_A = Column(Integer, nullable=False)
    number_of_pieces_B = Column(Integer, nullable=False)
    pieces_created_A = Column(Integer, default=0)
    pieces_created_B = Column(Integer, default=0)
    status = Column(String(256), nullable=False, default=STATUS_CREATED)


class Piece(BaseModel):
    __tablename__ = "piece"
    id = Column(Integer, primary_key=True)
    manufacturing_date = Column(DateTime(timezone=True), server_default=None)
    order_id = Column(Integer, nullable=True)
    type = Column(String, nullable=False)
