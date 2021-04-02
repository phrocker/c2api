import logging
import time
import os
import uuid
from flask import request
from flask_restplus import Resource
from c2api.api.api import api
from c2api.api.serializers import status,flowinfo
from flask import Response
from c2api.api import operations
from flask_restplus import reqparse
from c2api.config import current_config
from c2api.models import Heartbeat, AgentInfo, HostedFlows, FlowInfo, AgentClass
from flask import jsonify
from flask_restplus import fields
from c2api.models import db
from werkzeug.utils import secure_filename

log = logging.getLogger(__name__)

ns = api.namespace('update', description='Heartbeat Operations for Agents.')

@ns.route('/clear/connection/<agentid>/<queueid>')
@api.response(200, 'Connection clear initiated')
class ClearConnection(Resource):

    
    """
        This should be the endpoint to get missed heartbeats
    """
    @api.marshal_with(status)
    def post(self,agentid,queueid):
        arguments = dict()
        arguments["queueid"]=queueid
        id = operations.queue_operation("clear","connection",arguments)
        if id is not None:
            operations.assign_operation(id,agentid)
        ret = {'status':'clear initiated','identifier':id}
        return ret,200

@ns.route('/class/flow/<agentclass>')
@api.response(200, 'Flow update successful for the provided class ')
@api.response(400, 'Invalid request')
class UpdateFlow(Resource):

    
    """
        This should be the endpoint to get missed heartbeats
    """
    @api.marshal_with(status)
    @api.expect(flowinfo)
    def post(self,agentclass):
        content = request.json
        if content is None:
            ret = {'status':'invalid request','error': 'must supply input'}
            return ret,400
        ## expect bucketId, flowId, and registryUrl
        if content['flowId'] is None:
            ret = {'status':'invalid request','error': 'flowId is required'}
            return ret,400
        bucket_id = content.get('bucketId',"")
        registry_url = content.get('registryUrl',"")
        new_flow_id = content['flowId']
        new_flow_info = FlowInfo(flow_id=new_flow_id,bucketId=bucket_id,registry_url=registry_url)
        db.session.add(new_flow_info)
        db.session.commit()
        agent_class = AgentClass.query.filter_by(agent_class=agentclass).first()
        if agent_class is None:
            ret = {'status':'clear initiated','error': 'Invalid class'}
            return ret,400
        agent_class.flow_id = new_flow_id
        db.session.commit()
        ret = {'status':'Class updated'}
        return ret,200

@ns.route('/agent/<agentid>/<type>/component/<component_id>')
@api.response(200, 'Operation Successful')
@api.response(400, 'Invalid request')
class ComponentOperation(Resource):

    allowed_operations = ['stop','start']
    
    """
        This should be the endpoint to get missed heartbeats
    """
    @api.marshal_with(status)
    def post(self,agentid,type,component_id):
        content = request.json
        
        adjusted_type = type.lower()
        
        if adjusted_type not in self.allowed_operations:
            return {'status':'invalid request','error': 'Not a valid operation'},400
        
        agent = AgentInfo.query.filter_by(id=agentid).first()

        expected_type = "running"
        new_status = "stopped"
        if adjusted_type == "start":
            expected_type = "stopped"
            new_status = "running"


        if not agent:
            return {'status':'invalid request','error': 'agentid is not valid'},400

        for component in agent.component_statuses:
            if component.component_uuid == component_id and component.component_status == expected_type:
                ## we are running, so we can stop
                component.component_status=new_status
                db.session.commit()
                arguments = dict()
                id = operations.queue_operation(adjusted_type,component.component_name,arguments)
                operations.assign_operation(id,agentid)
                return {'status':'queued', 'identifier': id}, 200

@ns.route('/class/flow/<operation>/<agentclass>')
@api.response(200, 'Operation Successful')
@api.response(400, 'Invalid request')
class FlowOperation(Resource):

    allowed_operations = ['upload']
    
    """
        This should be the endpoint to get missed heartbeats
    """
    @api.marshal_with(status)
    def post(self,operation, agentclass):
        
        adjusted_operation = operation.lower()
        
        if adjusted_operation not in self.allowed_operations:
            return {'status':'invalid request','error': 'Not a valid operation'},400
        
        if adjusted_operation == "upload":
            new_flow = HostedFlows(uuid=str(uuid.uuid1()))
        
            filename = secure_filename(str(new_flow.uuid))
            filename = os.path.join(current_config.UPLOAD_FOLDER, filename)
            with open(filename, "w") as f:
                f.write(str(request.stream.read().decode('utf-8')))

            new_flow.flow=filename
            db.session.add(new_flow)
            db.session.commit()
            bucket_id = ""
            
            
            registry_url = request.host + "/api/query/flow/" + str(new_flow.id) + "/flows/" + new_flow.uuid + "/buckets/default"
            new_flow_id = new_flow.uuid
            new_flow_info = FlowInfo(flow_id=new_flow_id,bucketId=bucket_id,registry_url=registry_url)
            db.session.add(new_flow_info)
            db.session.commit()
            agent_class = AgentClass.query.filter_by(agent_class=agentclass).first()
            if agent_class is None:
                if operations.verify_class(agentclass): 
                    agent_class = AgentClass(agent_class=agentclass)
                    db.session.add(agent_class)
                else:
                    return {'status': 'invalid reqquest' , 'error':'Invalid class'},400
            agent_class.flow_id = new_flow_id
            db.session.commit()
            return {'status': 'Flowfile uploaded' },200
