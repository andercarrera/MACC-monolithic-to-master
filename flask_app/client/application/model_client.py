from sqlalchemy import Column, DateTime, Integer, String, TEXT, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
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


client_role_table = Table('client_role', Base.metadata,
                          Column('client_id', ForeignKey('client.id'), primary_key=True),
                          Column('role_id', ForeignKey('role.id'), primary_key=True)
                          )


class Client(BaseModel):
    STATUS_CREATED = "created"
    STATUS_CANCELLED = "cancelled"

    __tablename__ = "client"
    id = Column(Integer, primary_key=True)
    email = Column(TEXT, nullable=False, default="default@email.com")
    status = Column(String(256), nullable=False, default=STATUS_CREATED)
    username = Column(TEXT, nullable=False)
    password = Column(TEXT, nullable=False)
    roles = relationship("Role", secondary=client_role_table, back_populates="clients")


class Role(BaseModel):
    __tablename__ = "role"
    id = Column(Integer, primary_key=True)
    name = Column(TEXT, nullable=False)
    clients = relationship("Client", secondary=client_role_table, back_populates="roles")
