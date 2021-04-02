import time, base64
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref
from sqlalchemy import create_engine, ForeignKey, Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
db = SQLAlchemy()


class BuildInfo(db.Model):
    __tablename__ = "buildinfo"
    revision = db.Column(db.Text, primary_key=True)
    flags = db.Column(db.String(500), primary_key=True)
    compiler = db.Column(db.Text, primary_key=True)
    timestamp = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(255), primary_key=True)
    
    def __repr__(self):
        return '<BuildInfo %r, %r>' % self.revision, self.version

class OperationArguments(db.Model):
    __tablename__ = "operations_arguments"
    id = db.Column(db.Integer, db.Sequence('seq_reg_id', start=199, increment=1),
               primary_key=True)
    name = db.Column(db.String(80))
    value = db.Column(db.Text)
    operation_id = db.Column(db.Integer, ForeignKey("operations.id"))
    operation_info =  relationship("Operations", back_populates="operation_arguments")

class Operations(db.Model):
    __tablename__ = "operations"
    id = db.Column(db.Integer, db.Sequence('seq_reg_id', start=199, increment=1),
               primary_key=True)
    name = db.Column(db.String(80))
    operand = db.Column(db.Text)
    operation_arguments = relationship("OperationArguments", back_populates="operation_info")


class HostedFlows(db.Model):
    __tablename__ = "hostedFlows"
    id = db.Column(db.Integer, db.Sequence('seq_reg_id', start=199, increment=1),
               primary_key=True)
    uuid = db.Column(db.String(40))
    flow = db.Column(db.String(1024))


class AgentInfo(db.Model):
    __tablename__ = "agentinfo"
    id = db.Column(db.String(80), primary_key=True)
    agent_class = db.Column(db.String(80), ForeignKey("agentclass.agent_class"))
    flow_id = db.Column(db.String(80), ForeignKey("flowinfo.flow_id"))
    component_statuses = relationship("ComponentStatus", back_populates="agent_info")
    connection_statuses = relationship("ConnectionStatus", back_populates="agent_info")
    repository_statuses = relationship("RepositoryStatus", back_populates="agent_info")

    def __repr__(self):
        return '<AgentInfo %r %r>' % self.id, self.agent_class

class PendingOperations(db.Model):
    __tablename__ = "pending_operations"
    id = db.Column(db.Integer, db.Sequence('seq_reg_id', start=233, increment=1),
               primary_key=True)
    operation_id = db.Column(db.Integer, ForeignKey("operations.id"))
    agent_id = db.Column(db.String(80), ForeignKey("agentinfo.id"))
    status = db.Column(db.String(80), ForeignKey("operations.id"))
    
class AgentClass(db.Model):
    __tablename__ = "agentclass"
    agent_class = db.Column(db.String(80), primary_key=True)
    flow_id = db.Column(db.String(80), ForeignKey("flowinfo.flow_id"))


class FlowInfo(db.Model):
    __tablename__ = "flowinfo"
    flow_id = db.Column(db.String(80), primary_key=True)
    bucketId = db.Column(db.String(80), nullable=False)
    registry_url = db.Column(db.String(125), nullable=False)

    def __repr__(self):
        return '<FlowInfo %r %r>' % self.flow_id, self.registry_url


class ConnectionStatus(db.Model):
    __tablename__ = "connection_statuses"
    id = db.Column(db.Integer, db.Sequence('seq_reg_id', start=1, increment=1),
               primary_key=True)
    agent_info_id = db.Column(db.String(80), ForeignKey("agentinfo.id"))
    agent_info=  relationship("AgentInfo", back_populates="connection_statuses")
    component_name = db.Column(db.String(120), nullable=False)
    component_status = db.Column(db.String(5), nullable=False)
    component_uuid = db.Column(db.String(50), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    sizeMax = db.Column(db.Integer, nullable=False)
    data = db.Column(db.Integer, nullable=False)
    dataMax = db.Column(db.Integer, nullable=False)

class ComponentStatus(db.Model):
    __tablename__ = "component_statuses"
    id = db.Column(db.Integer, db.Sequence('seq_reg_id', start=1, increment=1),
               primary_key=True)
    agent_info_id = db.Column(db.String(80), ForeignKey("agentinfo.id"))
    agent_info=  relationship("AgentInfo", back_populates="component_statuses")
    component_name = db.Column(db.String(120), nullable=False)
    component_status = db.Column(db.String(5), nullable=False)
    component_uuid = db.Column(db.String(50), nullable=False)
    
class RepositoryStatus(db.Model):
    __tablename__ = "repository_statuses"
    id = db.Column(db.Integer, db.Sequence('seq_reg_id', start=1, increment=1),
               primary_key=True)
    agent_info_id = db.Column(db.String(80),  ForeignKey("agentinfo.id"))
    agent_info=  relationship("AgentInfo", back_populates="repository_statuses")
    type = db.Column(db.String(80), nullable=False)
    size = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<RepositoryStatus %r ( %r - %r ) >' % self.id, self.type, self.size



class Heartbeat(db.Model):
    __tablename__ = "heartbeats"
    id = db.Column(db.Integer, db.Sequence('seq_reg_id', start=1, increment=1),
               primary_key=True)
    operation = db.Column(db.String(80), unique=False, nullable=False)
    agent_id = db.Column(db.Integer, ForeignKey("agentinfo.id"))
    timestamp = Column(db.Integer, default=time.time()*1000)

    def __repr__(self):
        return '<Heartbeat %r %r>' % self.id, self.operation

### schema


class AgentInfoSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = AgentInfo;
        include_fk = True
        load_instance = True


class HeatBeatSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Heartbeat
        include_fk = True
        load_instance = True

class FlowIInfoSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = FlowInfo
        include_fk = True
        load_instance = True