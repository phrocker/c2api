import time
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from flask import Response
from flask import current_app
app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
from models import db ,Heartbeat, AgentInfo, FlowInfo, AgentClass
import operations
db.init_app(app)


@app.route('/')
def hello():
    return "Hello World!"

@app.route('/init')
def initdb():
    db.create_all()
    return "Initialized!"

@app.route('/api/clear/connection/<agentid>/<queueid>')
def clear_connection(agentid,queueid):
    arguments = dict()
    arguments["queueid"]=queueid
    id = operations.queue_operation("clear","connection",arguments)
    operations.assign_operation(id,agentid)
    return ""

@app.route('/api/update/class/flow/<agentclass>', methods=['POST'])
def update_class_flow(agentclass):
    content = request.json
    ## expect bucketId, flowId, and registryUrl
    if content['flowId'] is not None:
         Response("{'required_fields':'flowId'}", status=400, mimetype='application/json')
    bucket_id = content.get('bucketId',"")
    registry_url = content.get('registryUrl',"")
    new_flow_id = content['flowId']
    new_flow_info = FlowInfo(flow_id=new_flow_id,bucketId=bucket_id,registry_url=registry_url)
    db.session.add(new_flow_info)
    db.session.commit()
    agent_class = AgentClass.query.filter_by(agent_class=agentclass).first()
    if agent_class is None:
        Response("{'error':'Invalid class'}", status=400, mimetype='application/json')
    agent_class.flow_id = new_flow_id
    db.session.commit()
    return Response("{'status':'updated'}", status=200, mimetype='application/json')

@app.route('/api/update/agent/<agentid>/stop/component/<component_id>',  methods=['POST'])
def stop_component(agentid,component_id):
    content = request.json
    ## expect bucketId, flowId, and registryUrl
    agent = AgentInfo.query.filter_by(id=agentid).first()

    for component in agent.component_statuses:
        if component.component_uuid == component_id and component.component_status == "running":
            ## we are running, so we can stop
            component.component_status="stopped"
            db.session.commit()
            arguments = dict()
            id = operations.queue_operation("stop",component.component_name,arguments)
            operations.assign_operation(id,agentid)
            return Response("{'status':'queued'}", status=200, mimetype='application/json')
    return Response("{'status':'nochange'}", status=200, mimetype='application/json')

@app.route('/api/update/agent/<agentid>/start/component/<component_id>',  methods=['POST'])
def start_component(agentid,component_id):
    content = request.json
    ## expect bucketId, flowId, and registryUrl
    agent = AgentInfo.query.filter_by(id=agentid).first()

    for component in agent.component_statuses:
        if component.component_uuid == component_id and component.component_status == "stopped":
            ## we are running, so we can stop
            component.component_status="running"
            db.session.commit()
            arguments = dict()
            id = operations.queue_operation("start",component.component_name,arguments)
            operations.assign_operation(id,agentid)
            return Response("{'status':'queued'}", status=200, mimetype='application/json')
    return Response("{'status':'nochange'}", status=200, mimetype='application/json')

"""
    This should be the endpoint to get missed heartbeats
"""
@app.route('/api/query/missed')
def missed_heartbeat():
    max_heartbeat = current_app.config.get("max_heartbeat")
    if max_heartbeat is None:
        max_heartbeat = 100
    max_timestamp = time.time() * 1000 - max_heartbeat
    missed_heartbeats = Heartbeat.query.filter(Heartbeat.timestamp < max_timestamp).order_by(Heartbeat.timestamp.desc()).with_entities(Heartbeat.agent_id).distinct(Heartbeat.agent_id).all()
    hbs = []
    if missed_heartbeats is not None:
        for hb in missed_heartbeats:
            print(hb.agent_id + " " + str(max_timestamp))
            hbs.append( { "id" : hb.agent_id})
    return jsonify(hbs)

@app.route('/api/query/connections/<agentid>')
def list_connections(agentid):
    agent = AgentInfo.query.filter_by(id=agentid).first()
    connections = []
    if agent is not None:
        print ("we have " + agent.id)
        for connection in agent.connection_statuses:
            connection_status = dict()
            connection_status['name'] = connection.component_name 
            connection_status['uuid'] = connection.component_uuid
            connection_status['size'] = connection.size
            connection_status['sizeMax'] = connection.sizeMax
            connection_status['data'] = connection.data
            connection_status['dataMax'] = connection.dataMax
            connections.append(connection_status)
    else:
        print("don't have")
    return jsonify(connections)

@app.route('/api/query/components/<agentid>')
def list_components(agentid):
    agent = AgentInfo.query.filter_by(id=agentid).first()
    components = []
    if agent is not None:
        print ("we have " + agent.id)
        for component in agent.component_statuses:
            component_status = dict()
            component_status['name'] = component.component_name 
            component_status['uuid'] = component.component_uuid
            component_status['status'] = component.component_status
            components.append(component_status)
    else:
        print("don't have")
    return jsonify(components)

@app.route('/api/query/lastheard/<agent_id>')
def last_heard(agent_id):
    last_heartbeat = Heartbeat.query.filter_by(agent_id=agent_id).order_by(Heartbeat.timestamp.desc()).first()
    hb = dict()
    if last_heartbeat is None:
        return "{}"
    else:
        hb["agent_id"] = agent_id
        hb["last_heard"] = last_heartbeat.timestamp
        return jsonify(hb)

@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    content = request.json
    print(content)
    if content['operation'] is not None:
        if content['operation'] == "heartbeat":
            return operations.perform_heartbeat(content)
        if content['operation'] == "acknowledge":
            print(content)
            return operations.perform_acknowledge(content)
    Response("{'error':'Invalid heartbeat'}", status=400, mimetype='application/json')


if __name__ == '__main__':
    app.run()

