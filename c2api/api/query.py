import logging
import time
import os
from flask import request
from flask_restplus import Resource
from c2api.api.api import api
from c2api.api.serializers import last_heard_heartbeat, heartbeat, connection, component, agent_class
from flask import Response
from c2api.api import operations
from flask_restplus import reqparse
from c2api.config import current_config
from c2api.models import Heartbeat, AgentInfo, HostedFlows, FlowInfo
from flask import jsonify
from flask_restplus import fields
from sqlalchemy import func, and_
from c2api.models import db
log = logging.getLogger(__name__)

ns = api.namespace('query', description='Heartbeat Operations for Agents.')

@ns.route('/missed/')
@api.response(200, 'Returns an array of agent IDs that have missed a heartbeat.')
class MissedHeartbeat(Resource):

    
    """
        This should be the endpoint to get missed heartbeats
    """
    def get(self):
        max_heartbeat = current_config.MAX_HEARTBEAT
        if max_heartbeat is None:
            max_heartbeat = 100
        max_timestamp = time.time() * 1000 - max_heartbeat
        
        subq = (
            db.session
            .query(Heartbeat.agent_id, func.max(Heartbeat.timestamp).label("max_ts"))
            .group_by(Heartbeat.agent_id)
            .subquery()
        )

        query = (
            db.session.query(Heartbeat)
            .join(subq, and_(Heartbeat.agent_id == subq.c.agent_id,
                            Heartbeat.timestamp == subq.c.max_ts,
                            Heartbeat.timestamp < max_timestamp))
        )
        missed_heartbeats = query.all()

        hbs = []
        log.debug('>>>>> Max is {}, time now is {}'.format(max_timestamp, time.time()*1000))
        if missed_heartbeats is not None:
            for hb in missed_heartbeats:
                hbs.append( { "id" : hb.agent_id})
        return jsonify(hbs)

@ns.route('/agents/class/<agentclass>')
@api.response(200, 'Returns an array of Agents that exist within this class..')
class ListAgentsByClass(Resource):

    
    """
        This should be the endpoint to get missed heartbeats
    """
    @api.marshal_with(agent_class)
    def get(self, agentclass):
        agents = AgentInfo.query.filter_by(agent_class=agentclass).all()
        return agents

@ns.route('/connections/<agentid>')
@api.response(200, 'Returns an array of connections for the associated agent ID.')
@api.response(400, 'Agent ID does not exist')
class ListConnections(Resource):

    
    """
        This should be the endpoint to get missed heartbeats
    """
    @api.marshal_with(connection)
    def get(self, agentid):
        agent = AgentInfo.query.filter_by(id=agentid).first()
        if agent is not None and len(agent.connection_statuses) > 0:
            return agent.connection_statuses
        else:
            return {},400


@ns.route('/components/<agentid>')
@api.response(200, 'Returns an array of components for the associated agent ID.')
@api.response(400, 'Agent ID does not exist')
class ListComponents(Resource):

    
    """
        This should be the endpoint to get missed heartbeats
    """
    @api.marshal_with(component)
    def get(self, agentid):
        agent = AgentInfo.query.filter_by(id=agentid).first()
        if agent is not None and len(agent.component_statuses) > 0:
            return agent.component_statuses
        else:
            return None,400

@ns.route('/lastheard/<agentid>')
@api.response(200, 'Returns an array of components for the associated agent ID.')
@api.response(400, 'Agent ID does not exist')
class LastHeard(Resource):

    
    """
        This should be the endpoint to get missed heartbeats
    """
    @api.marshal_with(last_heard_heartbeat)
    def get(self, agentid):
        last_heartbeat = Heartbeat.query.filter_by(agent_id=agentid).order_by(Heartbeat.timestamp.desc()).with_entities(Heartbeat.agent_id, Heartbeat.timestamp).first()
        if last_heartbeat is not None:
            return last_heartbeat
        else:
            return None,400

@ns.route('/flow/<flowid>/flows/<uuid>/buckets/default')
@api.response(200, 'Returns an array of components for the associated agent ID.')
@api.response(404, 'Invalid Flow ID')
class DeliverFlow(Resource):

    
    """
        This should be the endpoint to get missed heartbeats
    """
    def get(self, flowid, uuid):
        hostedflow = HostedFlows.query.filter_by(id=flowid,uuid=uuid).first()
        if hostedflow is None:
            return Response("{'status':'missing'}", status=400, mimetype='application/json')
            
        flow = FlowInfo.query.filter_by(flow_id=hostedflow.uuid).first()
        if flow is None:
            return Response("{'status':'missing'}", status=400, mimetype='application/json')
        filename = os.path.join(current_config.UPLOAD_FOLDER, flow.flow_id)
        file = open(filename,mode='r')
        resp = file.read()
        file.close()
        return Response(resp, status=200, mimetype='multipart/form-data')

