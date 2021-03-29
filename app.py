import time
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
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

@app.route('/api/query/missed')
def missed_heartbeat():
    max_heartbeat = current_app.config.get("max_heartbeat")
    if max_heartbeat is None:
        max_heartbeat = 100
    max_timestamp = time.time() * 1000 - max_heartbeat
    #.filter(Heartbeat.timestamp < max_timestamp)
    #filter(Heartbeat.timestamp < max_timestamp).
    missed_heartbeats = Heartbeat.query.filter(Heartbeat.timestamp < max_timestamp).order_by(Heartbeat.timestamp.desc()).with_entities(Heartbeat.agent_id).distinct(Heartbeat.agent_id).all()
    hbs = []
    if missed_heartbeats is not None:
        for hb in missed_heartbeats:
            print(hb.agent_id + " " + str(max_timestamp))
            hbs.append( { "id" : hb.agent_id})
    return jsonify(hbs)

@app.route('/api/query/lastheard/<agent_id>')
def last_heard(agent_id):
    #.filter(Heartbeat.timestamp < max_timestamp)
    last_heartbeat = Heartbeat.query.filter_by(agent_id=agent_id).order_by(Heartbeat.timestamp.desc()).first()
    hb = dict()
    if last_heartbeat is None:
        return "{}"
    else:
        hb["agent_id"] = agent_id
        hb["last_haerd"] = last_heartbeat.timestamp
        return jsonify(hb)

@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    content = request.json
    if content['operation'] is not None:
        if content['operation'] == "heartbeat":
            return operations.perform_heartbeat(content)
        if content['operation'] == "acknowledge":
            print(content)
            return operations.perform_acknowledge(content)
    return "No Content"


@app.route('/<name>')
def hello_name(name):
    return "Hello {}!".format(name)

if __name__ == '__main__':
    app.run()

