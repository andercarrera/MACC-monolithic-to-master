from sqlalchemy import Column, DateTime, Integer, String, TEXT
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


class Delivery(BaseModel):
    STATUS_PREPARING = "preparing"
    STATUS_READY = "ready"
    STATUS_DELIVERED = "delivered"

    __tablename__ = "delivery"
    id = Column(Integer, primary_key=True)
    address = Column(TEXT, nullable=True, default=None)
    status = Column(String(256), nullable=False, default="preparing")
    order_id = Column(Integer, nullable=False)
